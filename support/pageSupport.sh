#!/bin/bash 

show_ip() {
    send "LN1=Interface re$1"
    ip=$(ifconfig ""re$1"" | grep inet | awk '{printf $2}')
    send "LN2=$ip"
}