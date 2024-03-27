#!/bin/bash
#
# Main Control script for Free/TrueNAS CORE & SCALE on Western Digital PR2100?/PR4100 
# Based off wdhws v1.0 by TFL (stefaang)
#
# wdpreinit V1.1 by Coltonton
#    - Fixed Some Typos/Cleaned up while I was here
#    - Added Support For TrueNAS Scale as well as TrueNAS CORE
#    - More Comments = More Better
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

###########################################################################
#############################   VARS   ####################################
###########################################################################
minfanspeed=30    # Minimum fan speed in percent
maxcputemp=80     # Maximum CPU temp before going full beans
opptemp=35        # Optimal (desired) temp (commie C degrees not freedom F :( )
tty=/dev/ttyS2    # Used to init variable, gets changed based on kernal in get_i2c_TTY()


###########################################################################
#############################   FUNCS   ###################################
###########################################################################
get_i2c_TTY(){
    getVer=$(uname -s)           # Get Linux Kernal (Linux vs FreeBSD for TrueNas Scal/Core)
    if [ $getVer == 'FreeBSD' ]  # If FreeBSD Free/TrueNAS Core
    then
        echo Found FreeBSD 
        tty=/dev/cuau3             # FreeBSD uses /dev/cuau3 for i2C coms
    elif [ $getVer == 'Linux' ]  # If Linux Free/TrueNAS Scale
    then
        echo Found Linux
        tty=/dev/ttyS2             # Linux uses much cooler (telatype) /dev/ttyS2 for i2C coms
    else                         # Just in case to catch wrong systems
        echo ERROR: Detected Kernal Type Does Not Match Any Supported By This Program
        echo Or there was an error
        exit 
    fi
}

setup_tty() {
    exec 4<$tty 5>$tty
}

setup_i2c() {
    # load kernel modules required for the temperature sensor on the RAM modules
    kldload -n iicbus smbus smb ichsmb
}

send() {
    setup_tty
    # send a command to the PMC module and echo the answer
    echo -ne "$1\r" >&5
    read ans <&4
    if [ "$ans" = "ALERT" ]; then
        echo -ne ALERT >&2
        exit 2 
    else
        # keep this for debugging failing commands
        if [ "$ans" = "ERR" ] || [ -z "$ans" ]; then
            echo "CMD $1 gives ERR at $2" >&2
            send_empty
            ans=$(send "$1" $(($2 + 1)))
            #exit 1
        fi
    fi
    # only echo the result for retries ($2 not empty)
    if [ ! -z $2 ]; then 
        echo "CMD $1 gives '$ans' at $2" >&2 
    fi 
    echo $ans
    send_empty
    # deconstruct tty file pointers, otherwise this script breaks on sleep 
    exec 4<&- 5>&-
}

send_empty() {
    # send a empty command to clear the output
    echo -ne "\r" >&5
    read ignore <&4
}

get_ncpu() {
    # get the number of CPUs
    sysctl -n hw.ncpu
}

get_coretemp() {
    # get the CPU temperature and strip of the Celsius
    sysctl -n dev.cpu.$1.temperature | cut -d'.' -f1
}

get_disktemp() {
    # get the disk $i temperature only if it is spinning
    smartctl -n standby -A /dev/ada0 | grep Temperature_Celsius | awk '{print $10}'
}

get_ramtemp() {
    # get the memory temperature from the I2C sensor
    smbmsg -s 0x98 -c 0x0$1 -i 1 -F %d
}

get_pmc() {
    # get a value from the PMC
    # e.g. TMP returns TMP=25 --> 25
    send $1 | cut -d'=' -f2
}

show_welcome() {
    # set welcome message
    # maximum  "xxx xxx xxx xxx " 
    send   "LN1=    FreeNAS     "
    send   "LN2=    Running     " 
}

led(){
    #echo "PowerMode:$1 - PowerColor:$2 - UsbMode:$3 - UsbColor$4"
    if [ "$1" == SOLID ]; then
        send BLK=00
        send PLS=00
        if [ "$2" == BLU ]; then
            send LED=01
        elif [ "$2" == RED ]; then
            send LED=02
        elif [ "$2" == PUR ]; then
            send LED=03
        elif [ "$2" == GRE ]; then
            send LED=04
        elif [ "$2" == TEA ]; then
            send LED=05
        elif [ "$2" == YLW ]; then
            send LED=06
        elif [ "$2" == WHT ]; then
            send LED=07
        fi
    fi
    if [ "$1" == FLASH ]; then
        send LED=00
        send PLS=00
        if [ "$2" == BLU ]; then
            send BLK=01
        elif [ "$2" == RED ]; then
            send BLK=02
        elif [ "$2" == PUR ]; then
            send BLK=03
        elif [ "$2" == GRE ]; then
            send BLK=04
        elif [ "$2" == TEA ]; then
            send BLK=05
        elif [ "$2" == YLW ]; then
            send BLK=06
        elif [ "$2" == WHT ]; then
            send BLK=07
        fi
    fi

    if [ "$1" == PULSE ]; then
        send PLS=01
        send LED=00
        send BLK=00
    fi  
}

show_ip() {
    send "LN1=Interface re$1"
    ip=$(ifconfig re$1 | grep inet | awk '{printf $2}')
    send "LN2=$ip"
}

monitor() {
    lvl="COOL"
    cpumaxtmp=0
    minfanspeed=30 #Percent
    maxcputemp=80 
    opptemp=35

    # check RPM (fan may get stuck) and convert hex to dec
    fan=$(get_pmc FAN)
    rpm=$((0x$(get_pmc RPM)))
    echo "Got rpm $rpm"
    if [ "$rpm" != ERR ]; then
        if [ "$rpm" -lt 400 ]; then
            echo "WARNING: low RPM - $rpm - clean dust!"
            led FLASH RED
        fi
    fi
    
    # check pmc  
    tmp=$((0x$(get_pmc TMP)))
    if [ "$tmp" -gt 64 ]; then
        pmclvl="HOT"
    fi

    # check disks [adjust this for PR2100!!]
    for i in 0 1 2 3 ; do
        tmp=$(get_disktemp $i)
        echo "disk $i is $tmp"
        if [ ! -z $tmp ] && [ "$tmp" -gt 40 ]; then
            echo "Disk $i temperature is $tmp" 
            lvl="HOT"
        fi
    done
    
    #                                                         max-opperating=a   fullfan-minfan=b    b/a= fan percent per degree
    # check cpu #max 80 #opp 35 1.5% for every degree above 30%      80-35=45         100-30=70     70/45=1.5   
    for i in $(seq $(get_ncpu)); do
        tmp=$(get_coretemp $((i-1)))
        echo "cpu $i is $tmp"
        if [ "$tmp" -gt 80 ]; then
            echo "CPU $i temperature is $tmp"
            lvl="HOT"
        fi
        if [ $tmp -gt $cpumaxtmp ]; then
            cpumaxtmp=$tmp
        fi
    done

    echo "CPU max temp is $cpumaxtmp"
    newtmp=$(($cpumaxtmp-$opptemp))
    setspeed=$(($newtmp*2+$minfanspeed-5))
    echo "speed should be: $setspeed%"
    if [ $setspeed -lt $minfanspeed ]; then
            setspeed=$minfanspeed
            echo "Fan speed below minimum, bumping to $minfanspeed%..."
    fi
 
    # check ram
    for i in 0 1; do
        tmp=$(get_ramtemp $i)
        echo "ram$i temp is $tmp"
        if [ "$tmp" -gt 40 ]; then
            echo "RAM$i temperature is $tmp"
            lvl="HOT"
        fi
    done 

    echo "Temperature LVL is $lvl"
    if [ "$lvl" == HOT ] ; then
        if [ "$fan" != 40 ]; then
            send FAN=64
            led FLASH RED
        fi
    else
        send FAN=$setspeed 
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

init() {
    get_i2c_TTY
    setup_tty
    setup_i2c

    echo "Getting system status and firmware!"
    send VER
    send CFG 
    send STA
    led SOLID BLU
    show_welcome
}


###########################################################################
#############################   MAIN   ####################################
###########################################################################
init

while true; do
    # adjust fan speed every 30 seconds
    monitor

    # check for button presses
    for i in $(seq 10); do 
        sleep 1
        check_btn_pressed
    done
done

