#!/bin/bash

#source support/support2.sh
#
# Main Control script for Free/TrueNAS CORE & SCALE on Western Digital PR2100?/PR4100 
# Based off wdhws v1.0 by TFL (stefaang)
#
# wdpreinit V1.2 beta by Coltonton @D3ADCRU7R
#    - I'm back working on this!
#    - Decided to skip finishing 1.1 and am just going to 1.2 to have more fun
#    - Code being rebassed with functions moved to librarys
#    - Update the temp profile adding the ability for the ram/disk temps to also set the fan speed not just the cpu temp
#    - Show the PCM Temp
#    - Updated the Send command to better allow debug print and returning properly (still needs some work)
#    - hopefully cleaned up send command to not go banannas
#  
# BSD 3 LICENSE (inherited from TFL)
# Thanks unix stackexchange question 231975 & github user @stefaang

############### COMMAND LIST ###############
# THING          COMMAND       USE
# FAN            FAN=64        Enter Hex value 01-64 (1-100%) Use at your own risk, only you can prevent forest fires
# USB/Power LED  LED=13        (See LED Guide)
# PowerLED-Pulse PLS=01        00-off 01-on (cant change color? is always blue?)
# PowerLED-Blink BLK=01        (See LED Guide)
# LCDBacklight   BKL=64        Enter Hex value 00-64 (0-100%)
#                
# 
# To complete?

################ LED GUIDE #################
#XX-usb/pwr
#00-off/off 01-off/blue 02-off/red 03-off/purple 04-off/green 05-off/teal 06-off/yellow 07-off/White
#08-red/off 09-red/blue 0A-red/red 0B-red/purple 0C-red/green 0D-red/teal 0E-red/yellow 0F-red/White
#10-blue/off 11-blue/blue 12-blue/red 13-blue/purple 14-blue/green 15-blue/teal 16-blue/yellow 17-blue/White
#18-purple/off 19-purple/blue 1A-purple/red 1B-purple/purple 1C-purple/green 1D-purple/teal 1E-purple/yellow 1F-purple/White


source support/hwSupport.sh
source support/pageSupport.sh
###########################################################################
#########################   DO NOT TOUCH   ################################
###########################################################################

# Hardware characteristics tuned off a stock WDPR4100 with 4x WD Red Pro 18TB's. Running no VMs or Services just 2x SMB shares a IDLE.  
# This default profile optimizes for fan at 50% (pretty quiet with stock fan) while idleing
# Of course the device can run cooler, however that means more fan. Ideally fan value should not fluctuate much at idle
declare -A hwSaftey=(   [fanSpeedMinimum]=35  # Minimum allowed fan speed in HEX expressed as percent 0xXX
                        [cpuOptimalTemp]=35   # Optimal (desired) temp for CPU (commie C degrees not freedom F :()
                        [cpuMaxTemp]=80       # Maximum CPU temp before going full beans
                        [diskOptimalTemp]=35  # My disks tend to spin at idle at 35
                        [diskMaxTemp]=45      # Maximum DISK temp before going full beans
                        [diskDangerTemp]=60   # Absolute limit (minus saftey factor) before disk damage (65 for WD Red Pro) 
                        [pmcMaxTemp]=64       # Maximum PMC temp before going full beans
                        [ramMaxTemp]=40       # Maximum RAM temp before going full beans
                        [updateRate]=10       # How often in seconds to update hardware stats    
                        [hwOverTempAlarm]=0   # Alarm for when a piece of hardware is over temp.
                        

)

###########################################################################
#############################   VARS   ####################################
###########################################################################              
declare -A hwOverTempArray=()   # Array containing all devices that are overtemp
hwBayHD=()           # Array containing all the drives that are in a bay
hwExtraHDD=()        # Array for extra hard drives

declare -A sysInfo=([hwSystem]=Linux       # Used to init kernal variable, gets changed based on kernal in get_sys_info()
                    [hwTTY]=/dev/cuau3     # Used to init tty variable, gets changed based on kernal in get_sys_info()
                    [hwCPUCoreCount]=4     # Count of how many CPU cores there are
)
declare -A datetime=([Month]=01 
                    [Day]=01   
                    [Year]=00       
                    [Hour]=12      
                    [Minute]=00      
                    [Second]=00
)


###########################################################################
#############################   FUNCS   ###################################
###########################################################################

check_for_dependencies(){   # Simple just-to-be-safe check that SMART Mon exists
    depenflag=0
    # S.M.A.R.T Drive Utilities
    smartctl -v >/dev/null
    if [[ $? != 1 ]]; then
        printf "\n** SMART not installed please run - sudo apt install smartmontools ** \n\n "
        (( depenflag += 1 ))
    fi

    # lm-Sensors (For temp sensor data )
    sensors -v >/dev/null
    if [[ $? != 0 ]]; then
        printf "\n** lm-sensors not installed please run - sudo apt install smartmontools ** \n\n "
        (( depenflag+=2 ))
    fi
    
    if [ $depenflag -gt 0 ]; then
        #printf "Would you like me to install? y/n:"
        #read resp
        #if [[ $resp == "y"] && [ $depenflag -gt 0 ]; then
        #    if [ $depenflag -eq 1 ]; then
        #        sudo apt install smartmontools
        #    elif [ $depenflag -eq 2 ]; then
        #        sudo apt install lm-sensors
        #    elif [ $depenflag -eq 3 ]; then
        #        sudo apt install smartmontools && sudo apt install lm-sensors
        #    fi
        #fi
        printf "\n\n## PROGRAM TERMINATED ##\n\n"
        exit
    fi
}

get_sys_info(){         # Get system info based off kernal, as BSD/LINUX has not the same commands
    case "$( uname -s )" in        # Get Linux Kernal (Linux vs FreeBSD for TrueNas Scale/Core)
        Linux*)  sysInfo[hwSystem]=Linux;;
        *BSD)	 sysInfo[hwSystem]=BSD;;
        Darwin*) sysInfo[hwSystem]=MacOS;;
        CYGWIN*) sysInfo[hwSystem]=Cygwin;;
        MINGW*)  sysInfo[hwSystem]=MinGw;;
        *)       sysInfo[hwSystem]="Other"
    esac
    if [[ ! ${sysInfo[hwSystem]} =~ Linux|BSD ]]; then  # If system is not Linux or *BSD Show unsupported message
        echo "Sorry, This software version for the WD PR4100 Hawrdware does not support $hwSystem platform."
        echo "Please create an issue on Github to see about gettin support added"
        exit 1
    fi          
    if [ "${sysInfo[hwSystem]}" == BSD ]; then      # If *BSD Free/TrueNAS Core
        echo '# GETINFO: Detected BSD Kernal #'      # Show what kernal was identified
        sysInfo[hwTTY]=/dev/cuau3                    # FreeBSD uses /dev/cuau3 for i2C comms to PR4100 front hardware
        get_int_drives                      # Get location of ONLY internal bay drives
        sysInfo[hwCPUCoreCount]=$(sysctl -n hw.ncpu) # Get how many CPU cores
    elif [ ${sysInfo[hwSystem]} == Linux ]; then  # If Linux Free/TrueNAS Scale
        echo '# GETINFO: Detected Linux Kernal #'    # Show what kernal was identified
        sysInfo[hwTTY]=/dev/ttyS2                    # Linux uses much cooler (telatype) /dev/hwTTYS2 for i2C comms to PR4100 front hardware
        get_int_drives                      # Get location of ONLY internal bay drives
        sysInfo[hwCPUCoreCount]=$(nproc)             # Get how many CPU cores
    fi
    export sysInfo                          #Export sysInfo so our helper can pick it up
}

get_int_drives(){       # Basicly just gets the location of the internal bay HDD's
    for file in /dev/disk/by-id/ata*       # With each HDD decice thats ata (Internal Sata)
    do
        if [[ $file != *"-part"* ]]; then  # Filter out '-part$' devices as they are the same
            tmparr+=( $( ls -l "/dev/disk/by-id/ata-${file:20:100}" | awk '{print $11}' | cut -b 7-10 )  ) # Get the /dev location
            readarray -t hwBayHD < <(for a in "${tmparr[@]}"; do echo "/dev/$a"; done | sort) # Sort
        fi
    done
    echo "# GETINFO: Detected internal bay drives: ${hwBayHD[@]} #"
}

setup_i2c() {           # load kernel modules required for the temperature sensor on the RAM modules, only avalible on FreeNAS CORE
    if [ ${sysInfo[hwSystem]} == BSD ]; then
        kldload -n iicbus smbus smb ichsmb
    fi
}

get_datetime() {        # Duh.... Sorry lol, easy time/date vars cuz cleaner
    datetime[Month]=$(date +"%m")
    datetime[Day]=$(date +"%d")
    datetime[Year]=$(date +"%y")
    datetime[Hour]=$(date +"%H")
    datetime[Minute]=$(date +"%M")
    datetime[Second]=$(date +"%S") 
}

get_pmc() {             # Requires input - Get a value from the PMC ex. inputing RPM gets fan0's rpm
    send $1 1 | cut -d'=' -f2
}

get_disktemp() {        # Requires input - Get the disks temperature only if it is active, else return status
    drivesel=$1                       # For some reason I need this and cant put it in later? Makes i2c break somehow...
    smartctl -n standby -A $drivesel > /dev/null # Run command to get disk status
    getstatus=$(echo $?)              # Get drive exit status
    if [ "$getstatus" == "0" ]; then  # If the status of the drive is active, get its temperature
        smartctl -n standby -A $drivesel | grep Temperature_Celsius | awk '{print $10}'
    else                              # If the status of the drive is not active, return the exit status of the drive. Maybe its asleep/standby                
        return $getstatus
    fi
}

get_cpucoretemp() {     # Requires input - Get the specified CPU core temperature and strip off the celsius unit
    if [ ${sysInfo[hwSystem]} == BSD ]; then       #FreeNAS Core
        sysctl -n dev.cpu.$1.temperature | cut -d'.' -f1
    elif [ ${sysInfo[hwSystem]} == Linux ]; then   # TrueNAS Scale
        sensors | grep "Core $1" | awk '{print $3}' | cut -d'.' -f1 | cut -b 2-3
    fi  
}

get_ramtemp() {         # Requires input - Get the memory (ram) temperature from the I2C sensor FREENAS CORE ONLY
    if [ ${sysInfo[hwSystem]} == BSD ]; then
        smbmsg -s 0x98 -c 0x0$1 -i 1 -F %d
    elif [ ${sysInfo[hwSystem]} == Linux ]; then
        return "0"
        # sensors | grep "temp1" | awk '{print $2}' | cut -d'.' -f1 | cut -b 2-3
    fi
}

updateHW() {             # Main Function - Does all the hardware updating.
    hottestCoreTemp=0
    hottestDiskTemp=0
    hottestRamTemp=0
    clear -x
    prevFanHex=$requestFan
  # check RPM (fan may get stuck) and convert hex to dec
    #readfanpercent=$(get_pmc FAN)
    rpmOutput=$(get_pmc "RPM")
    rpmhex=${rpmOutput: -4}
    rpmdec=$((0x$rpmhex))
    echo "FAN0 RPM is: $rpmdec"    
    if [ "$rpmhex" == "ERR" ]; then   # NEED TO ADD ERROR BACK
        if [ "$rpmdec" -lt 400 ]; then
            echo "ERROR FAN0 RPM: low RPM - $rpmdec - clean dust!"
        else
            echo "ERROR FAN0: Generic"
        fi
        hwSaftey[hwOverTempAlarm]=1  # Cause a over temperature Alarm
    fi
    
  # Check the Temperature of the PMC and convert to hex 
    pcmOutput=$(get_pmc TMP)   # I dont need to do this in 2 steps but VSCode complains soooooo..... 2 steps wowww 
    pcmhex=${pcmOutput: -2}
    pcmdec=$((0x$pcmhex))   # use tmpdec=$((0x$(get_pmc TMP))) if you want, it works, i just hate the 'error'
    echo "PCM is: $pcmdec °C" 
    if [ "$pcmdec" -gt ${hwSaftey[pmcMaxTemp]} ]; then
        echo "WARNING: PMC surpassed maximum (${hwSaftey[pmcMaxTemp]}°C), full throttle activated!"
        hwSaftey[hwOverTempAlarm]=1 
        #hwOverTempArray+=("PMC $tmp°C/$pmcMaxTemp°C")"
    fi

  # Check the Hard Drive Temperature [adjust this for PR2100!!] (<- IDK what that means)
    
    printf "|------ DISK TEMPS ------\n"
    for i in "${hwBayHD[@]}" ; do
        tmp=$(get_disktemp $i)
        waserror=$(echo $?)
        if [ $waserror -ne "0" ]; then
            if [ $waserror == 2 ]; then
                ret=standby
            else
                ret=Error
            fi
            echo "| Drive ${i:5:5} is in $ret status"
        else
            echo "| Drive ${i:5:15} is $tmp °C"
            if [ ! -z $tmp ] && [ $tmp -gt ${hwSaftey[diskMaxTemp]} ]; then
                echo "| WARNING: CPU Core$i surpassed maximum (${hwSaftey[diskMaxTemp]}°C), full throttle activated!" 
                hwSaftey[hwOverTempAlarm]=1
                hwOverTempArray+=("HDD$i $tmp°C/$hddMaxTemp°C")
            fi
        fi
        if [ $tmp -gt $hottestDiskTemp ]; then
            hottestDiskTemp=$tmp
        fi  
    done
    echo "| Hottest disk is $hottestDiskTemp °C"
    printf "|------------------------\n"
    
  # Check the Temperature of the CPU
    printf "|---- CPU CORE TEMPS ----\n"
    for i in $(seq ${sysInfo[hwCPUCoreCount]}); do
        tmp=$(get_cpucoretemp $((i-1)))
        echo "| cpu core$i is $tmp °C"
        if [ $tmp -gt ${hwSaftey[cpuMaxTemp]} ]; then
            echo "| WARNING: CPU Core$i surpassed maximum (${hwSaftey[cpuMaxTemp]}°C), full throttle activated!"
            hwOverTempArray+=("CPU$i $tmp°C/$cpuMaxTemp°C")
            hwSaftey[hwOverTempAlarm]=1
        fi
        if [ $tmp -gt $hottestCoreTemp ]; then
            hottestCoreTemp=$tmp
        fi
    done
    echo "| Hottest core is $hottestCoreTemp °C"
    printf "|------------------------\n"
 
  # Check the installed RAM Temperature
    printf "|------ RAM TEMPS -------\n"
    if [ ${sysInfo[hwSystem]} == BSD ]; then      # If *BSD Free/TrueNAS Core
        for i in 0 1; do
            tmp=$(get_ramtemp $i)
            echo "| ram$i temp is $tmp °C"
            if [ "$tmp" -gt ${hwSaftey[ramMaxTemp]} ]; then
                echo "| WARNING: RAM$i surpassed maximum (${hwSaftey[ramMaxTemp]}°C), full throttle activated!"
                hwOverTempArray+=("RAM $tmp°C/$ramMaxTemp°C")
                hwSaftey[hwOverTempAlarm]=1
            fi
            if [ $tmp -gt $hottestRamTemp ]; then
                hottestRamTemp=$tmp
            fi
        done 
    elif [ ${sysInfo[hwSystem]} == Linux ]; then  # If *Linux TrueNAS Scale 
        echo "|  Unsupported (Scale)"
        hottestRamTemp=0
    fi
    printf "|------------------------\n"

  # Get Desired Fans per each device (DISK, RAM, CPU)
    requestFan=0

    # The way the cooling profile works is liniar - basicly what we are doing here is taking the diffrence between
    # The full fan % and the minimum fan % to get (A) then we take the diffrence between the Max allowed temp
    # and the optimal temp to get (B) and finillay Dividing B by A. This gives us a value that represents how
    # many fan percent points each degree of the device represents.  
    # Basiclly   xMultiplier=((100 - fanSpeedMinimum) / (xMaxTemp - xOptimalTemp)) 
    # Or for core using the default values    coreMultiplier=((100 - 53) / (80 - 35)) == coreMultiplier=( 47 / 45 ) == coreMultiplier=1 (as there are no decimals)
    coreMultiplier="$(( ( 100 - $((0x${hwSaftey[fanSpeedMinimum]})) ) / ( ${hwSaftey[cpuMaxTemp]} - ${hwSaftey[cpuOptimalTemp]} ) ))" 
    diskMultiplier="$(( ( 100 - $((0x${hwSaftey[fanSpeedMinimum]})) ) / ( ${hwSaftey[diskMaxTemp]} - ${hwSaftey[diskOptimalTemp]} ) ))"

    #CPU CORE FAN REQUEST
    coreDiffTemp=$(("$hottestCoreTemp"-"${hwSaftey[cpuOptimalTemp]}"))                  # The temp of the hottest core minus the optimal temp to get how much hotter from the minimum
    requestFanCore=$(("$coreDiffTemp"*$coreMultiplier+"${hwSaftey[fanSpeedMinimum]}"))  # The diff times(*) the multiplier and add(+) the minimum fan speed
    requestFan=$requestFanCore                                                          # Set the gotten value to the requestFan Var
    echo "| Core request fan speed $((0x$requestFanCore))% [0x$requestFanCore]"
    
    # DISK FAN REQUEST
    diskDiffTemp=$(("$hottestDiskTemp"-"${hwSaftey[diskOptimalTemp]}"))                 # The temp of the hottest disk minus the optimal temp to get how much hotter from the minimum
    requestFanDisk=$(("$diskDiffTemp"*$diskMultiplier+"${hwSaftey[fanSpeedMinimum]}"))  # The diff times(*) the multiplier and add(+) the minimum fan speed
    if [ $requestFanDisk -gt $requestFan ]; then                                        # If this number is > requestFanCore Set the gotten value to the request Fan Var                          
        requestFan=$requestFanDisk
    fi
    echo "| Disks request fan speed $requestFanDisk% [0x$requestFanDisk]"

    # RAM FAN REQUEST
    # Activate only on TrueNas Core
    if [ ${sysInfo[hwSystem]} == BSD ]; then    
        ramDiffTemp=$(("$hottestRamTemp"-"${hwSaftey[cpuOptimalTemp]}"))  # The temp of the hottest disk minus the optimal temp to get how much hotter from the minimum
        requestFanRam=$(("$ramDiffTemp"*2+"$fanspeedmindec"-5))           # The diff times(*) the multiplier and add(+) the minimum fan speed
        if [ $requestFanRam -gt $requestFan ]; then                       # If this number is > requestFanCore && requestFanDisk Set the gotten value to the request Fan Var                          
            requestFan=$requestFanRam
        fi
        echo "| Ram request fan speed $((0x$requestFanRam))% [0x$requestFanRam]"
    # If TrueNAS Scale, this function is not supportd so do nothing
    else
        echo "| Ram can not request fan speed"
        requestFanRam=0
    fi
    printf "|------------------------\n"

  # Got all values, time to set Fan%
    
    if [ ${hwSaftey[hwOverTempAlarm]} -eq 1 ]; then  
    # If there is an active OverTemp Alarm 
        echo " WARNING: SYSTEM OVER LIMIT TEMPERATURE(s) FAN SET TO 100% [0x64]"
        echo "${#hwOverTempArray[@]}"   # Display the devices that are in an alarm state
        #hwLastOverTemp=$(get_datetime) # Save the time when the system over temped
        send FAN=64                     # Full Beans Fan 100% (0x64)
        set_pwr_led FLASH RED           # Flash Power LED RED to warn
        #write_logdata                  # OOOOO am I leaking future stuff?! 
    
    else 
    # There is no over temp condion
        #tempvar=$((0x$requestFanDisk))
        if [ $requestFan -lt ${hwSaftey[fanSpeedMinimum]} ]; then # If the desired fan speed is bellow minimum
            echo "Calculated fan speed below minimum allowed ($((0x$requestFan))%) [0x$requestFan], forcing $((0x${hwSaftey[fanSpeedMinimum]}))% [0x${hwSaftey[fanSpeedMinimum]}]..."
            requestFan=${hwSaftey[fanSpeedMinimum]}      # Set the fan to the min allowed
            send FAN=$requestFan                         # Set fan to mathed speed if not overtemped
        elif [ "$requestFan" != "$setspeedpre" ]; then # If the desired fan % changed from lasttime
            echo "Setting fan speed to: $((0x$requestFan))% [0x$requestFan] | Previous: $((0x$prevFanHex))% [0x$prevFanHex]"
            send FAN=$requestFan                         # Set fan to mathed speed if not overtemped
        fi
    fi
}



check_btn_pressed() {
    btn=$(get_pmc ISR) 
    #echo "Btn is .$btn."
    
    case $btn in
    20*)
        echo "Button up pressed!"
        menu=$(( ($menu + 1) % 3 ))
        ;;
    40*) 
        echo "Button down pressed!"
        menu=$(( ($menu + 2) % 3 ))
        ;;
    *)
        return    
    esac
    
    case "$menu" in
    0)
        show_welcome
        ;;
    1)
        show_ip 0
        ;;
    2)
        show_ip 1
        ;;
    # if you add menu items here, update mod 3 uses above    
    esac        
}

preload(){
    set_pwr_led PULSE BLU                     # Set the Power LED to flash yellow as visual indicator
    setDisplay "wdhardware.sh" "Starting..."  # Set front panel LCD Line 1 and 2
}

init() {
    clear -x
    get_sys_info
    preload
    sleep 2

    check_for_dependencies
    setup_i2c
    StartWDHW
    
    echo "Loading wdhws..."
    sleep 2
    setDisplay "TrueNAS" "Running"
    set_pwr_led SOLID BLU
    printf "# INIT DONE # \n\n"
}

###########################################################################
#############################   MAIN   ####################################
###########################################################################

init

while true; do
    # adjust fan speed every 10 seconds
    #echo "SUB"
    #echo $WDHardwareScriptOnline
    #WDHardwareScriptOnline=1
    updateHW
    echo -n "${hwSaftey[updateRate]} seconds until next hardware refresh"


    # check for button presses
    for i in $(seq ${hwSaftey[updateRate]}); do 
        sleep 1
        check_btn_pressed
    done
done