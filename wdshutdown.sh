#!/bin/bash
#
# Shutdown script for FreeNAS on Western Digital PR2100/PR4100 
# Based off wdhws v1.0 by TFL (stefaang)
# wdshutdown V1.0 by Coltonton
# 
# BSD 3 LICENSE (inherited from TFL)
#
# thanks unix stackexchange question 231975 & github user @stefaang

################ LED GUIDE ################
#XX-usb/pwr
#00-off/off 01-off/blue 02-off/red 03-off/purple 04-off/green 05-off/teal 06-off/yellow 07-off/White
#08-red/off 09-red/blue 0A-red/red 0B-red/purple 0C-red/green 0D-red/teal 0E-red/yellow 0F-red/White
#10-blue/off 11-blue/blue 12-blue/red 13-blue/purple 14-blue/green 15-blue/teal 16-blue/yellow 17-blue/White
#18-purple/off 19-purple/blue 1A-purple/red 1B-purple/purple 1C-purple/green 1D-purple/teal 1E-purple/yellow 1F-purple/White

setup_tty() {
    tty=/dev/cuau3
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

show_msg() {
    # set welcome message
    # maximum  "xxx xxx xxx xxx " 
    send   "LN1=    FreeNAS     "
    send   "LN2= Shutting Down  " 
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

###########################################################################
#############################   MAIN   ####################################
###########################################################################
setup_tty
setup_i2c

led FLASH YLW
show_msg


