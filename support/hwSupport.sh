#!/bin/bash 

set_pwr_led(){
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

setDisplay() {
    # Set Display Text
    # maximum  "xxx xxx xxx xxx "(16 chars) 
    maxlineWidth=16
    line1Output="LN1="
    line2Output="LN2="
    line1="${1:="                "}"
    line2="${2:="                "}"
    line1Len=${#line1}
    line2Len=${#line2}
    if ($line1Len > $maxlineWidth)
    then
        line1="${line1:0:15}"
    else
        line1Output+=$(printf "%*s\n" $(( (${#line1} + maxlineWidth) / 2)) "$line1")
    fi
    if ($line2Len > $maxlineWidth)
    then
        line2Output="${line2:0:15}"
    else
        line2Output+=$(printf "%*s\n" $(( (${#line2} + maxlineWidth) / 2)) "$line2")
    fi
    
    send "$line1Output"
    send "$line2Output" 
}

StartWDHW(){
    setup_tty
    echo "# GETINFO: Getting system status and firmware! *"
    send VER
    send CFG 
    send STA
}

setup_tty() {           # Start i2c
    #hwTTY="${sysInfo[hwTTY]}"
    #exec 4<$hwTTY 5>$hwTTY
    exec 4</dev/ttyS1 5>/dev/ttyS1
}


send() {                # Requires input - i2C send function to send commands to front panel
    setup_tty
    # send a command to the PMC module and echo the answer
    echo -ne "$1\r" >&5
    read -r ans <&4
    #if [ "$ans" = "ALERT" ]; then
    #    echo -ne ALERT >&2
    #    exit 2 
    #else
        # keep this for debugging failing commands
    #    if [ "$ans" = "ERR" ] || [ -z "$ans" ]; then
    #        echo "CMD $1 gives ERR at $2" >&2
    #        send_empty
    #        ans=$(send "$1" $(($2 + 1)))
    #        #exit
    #        exit 1
    #    fi
    #fi
    # only echo the result for retries ($2 not empty)
    if [ -n $((2)) ]; then 
        echo "CMD $1 gives '$ans' at $2" >&2 
    else
        echo "CMD $1 gives ERR at $2" >&2
    fi
    echo $((ans))
    
    send_empty
    # deconstruct tty file pointers, otherwise this script breaks on sleep 
    exec 4<&- 5>&-

}

send_empty() {          # i2c send blank to clear front panel input
    # send a empty command to clear the output
    echo -ne "\r" >&5
    # shellcheck disable=SC2034
    read -r ignore <&4
}