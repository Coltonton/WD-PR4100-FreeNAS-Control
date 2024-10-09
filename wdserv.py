#### /mnt/pool/py/bin/python3 /home/admin/wddhw/wdserv.py
import time
from datetime import datetime as clock



###########################################################################
#############################   VARS   ####################################
###########################################################################
upPushed = False
usbPushed = False
downPushed = False

lstupdatetime=""
lstvalue=""
Alert="0"

MailToSend=False
BackendStatus=""
Handshake=False

dbgn = "none"
dbgi = "info"
dbgd = "debug"
dbga = "all"
debugPrint="all"


###########################################################################
#############################   FUNCS   ###################################
###########################################################################
def dprint(pnt="", lvl=dbgn, tme=True, eod=False):   #Debug printing   pass in dbgn for none - dbgi for info - dbgd for debug and dbga for all
    #Debug Print is a routien to be able to select vebosity of output
    if tme == True:
        print(clock.now().strftime("===========\n† %m/%d %I:%M.%S[") + lvl + "," + debugPrint + "]")
    
    if type(pnt) == list:
        i=0
        print("‡ ", end='' )
        for x in pnt:
            print( pnt[i], end='' )
            i += 1
        endprint=False
    elif ((debugPrint == lvl or debugPrint == dbga) and (type(pnt) == str) and pnt):
        print("‡ " + pnt + "\n", end='')
        endprint=True

    if eod == True:
        print("⸸\n")

def backendHealthCheck():
    global BackendStatus
    file1 = open("daemon.txt", "r")
    f = file1.readlines()
    file1.close()

    Status = str(f[0]).rstrip('\n')

    if Status == "OFFLINE":
            BackendStatus="OFFLINE"
            time.sleep(1)

            return BackendStatus
    else:
        BackendStatus="ONLINE"
        time.sleep(1)
        return BackendStatus

def checkForIncomingMail():
    global lstupdatetime, Alert
    try:
        file1 = open("daemon.txt", "r")
        f = file1.readlines()
        Status = str(f[1]).rstrip('\n')
        file1.close()
        checklstupdatetime=str(f2)
        #print('Time was loaded [' + str(f2) + "]")
    except:
        f2=""
        checklstupdatetime=""
        #print('Time WAS NOT loaded correctly')

    print(f)
    if str(f[0]).rstrip('\n') == "OFFLINE":
        print("WARNING BACKEND SERVER WENT/IS OFFLINE")
        quit()

    if checklstupdatetime != lstupdatetime and checklstupdatetime:
        lstupdatetime = checklstupdatetime
        print("\n#################\ndata updated at [" + str(checklstupdatetime) + "], fetching...")
        try:
            file1 = open("daemon.txt", "r")
            f = file1.readlines() 
            Status = str(f[0]).rstrip('\n')
            vTime  = str(f[1]).rstrip('\n')
            Hex    = str(f[2]).rstrip('\n')    # RRRRLLTT BBLLKPDP  RPM,Level,temp,  Backlight,LED,Blink,Pulse,Drives,PSU
            Alert  = str(f[3]).rstrip('\n')
            file1.close()
            lstvalue = str(Hex)
            print('# Following data was loaded: \n  [' + str(Hex) + "]\n  " + str(Alert) + "\n")
        except:
            f1=""
            #print('Data WAS NOT loaded')
        

        if Alert == "1":
            print("## BUTTON PUSHED! " + str(Alert) + "\n\n\n")

        

def Send(snd):   
    with open('daemonin.txt', 'r') as file:
        data = file.readlines()
    file.close

    data = "ONLINE\nCMD\n" + snd

    print("Sending: " + snd)
    with open('daemonin.txt', 'w') as file:
        file.writelines( data )
    file.close

    i=0
    while True:
        
        time.sleep(1)
        with open('daemonin.txt', 'r') as file:
            data = file.readlines()
        file.close

        if data[1].rstrip('\r\n') == "ACK":
            datav = "ONLINE\nCMD\n\n"
            with open('daemonin.txt', 'w') as file:
                file.writelines( datav )
            file.close
            print("ACK\n")
            return True
        else: 
            i = i + 1
            if i > 5:
                print("Server Did not respond in 5 seconds...\n")
                checkForIncomingMail()
                #return False

        
def servOffline():
    data = "OFFLINE\n\n\n"
    #print(data)

    with open('daemonin.txt', 'w') as file:
        file.writelines( data )
    file.close
###########################################################################
#############################   MAIN   ####################################
###########################################################################
def execute_app():
    time.sleep(1)
    count = 0
    print("Program Status: [ONLINE]")
    while True:
        count = count + 1 
        backend=backendHealthCheck()
        if count > 60:
            print("Backend server failed to come online after 60 seconds... exiting...")
            quit()

        if backend == "ONLINE":
            print("Backend Server Status: [ONLINE] - Took [" + str(count) + "] Seconds")
            Handshake = Send("LED=04")
            print(Handshake)
            while True:
                Handshake = Send("LED=04")
                time.sleep(5)
                checkForIncomingMail()
                #Send("LED=03")
                #time.sleep(5)
            
def main():
    try:
        execute_app()
    finally:
        servOffline()


if __name__=='__main__':
    main()








################ NOTES ############

# DE0                                  4321
#  11111111 [FF] (Turns All Bays On)
#  11110000 [F0] (turns all bayys Off) 1

#  1000000 (turns Bays 1&2 Red)              ccccpppp
#                                                                                 43214321       
#  11001100 (turns 3&4 Blue | 1&2 Red)      00110011 (turns 1&2 Blue | 3&4 Red)   00101111 (turns 2 Blue | 1&3&4 Red ) - (or off if no drive)

# 00001111 ( Does Nothing)

# 10100101  Red Off Red Off        10101010[AA] red blue red blue 01010101[55] blue red blue red   11111010 off blue off blue




'''Depricated Funcs
def checkFanRPM():           #DEPRICATED
    send("RPM")
    #data=int(getResponce()[4:], 16)
    data=getResponce()[4:]
    print("## RPM FAN[0]: " + str(data))
    return data
def checkFanSpeed():         #DEPRICATED
    send("FAN")
    #data=int(getResponce()[4:], 16)
    data=getResponce()[4:]
    print("## SPEED FAN[0]: " + "00" + str(data))
    return data
def checkFan():              #DEPRICATED
    send("RPM")
    rpmhex=getResponce()[4:]
    send("FAN")
    speedhex=(getResponce()[4:]).zfill(4)
    datahex=(str(rpmhex) + str(speedhex)).capitalize()
    print("## FAN[0]: " + datahex.capitalize())
    return datahex
def checkLEDState():         #DEPRICATED
    leddict={"LED":"01", "BLK":"01", "PLS":"00"}

    send("LED")
    leddata=getResponce()[4:]   #01
    send("BLK")
    blkdata=int(getResponce()[4:])   #01
    send("PLS")
    plsdata=int(getResponce()[4:])   #00
    ledhex=(str(leddata)+ str(blkdata)+ str(plsdata))

    print("## LED State: " + str(ledhex))
    #print("## LED Blink State: " + str(blkdata))
    #print("## LED Pulse State: " + str(plsdata))
    return ledhex
def checkBacklight():        #DEPRICATED
    send("BKL")
    data=(getResponce()[4:]).zfill(4)
    print("## Backlight State: " + str(data))
    return data
def checkActuvePSUs():       #DEPRICATED  #Catches Here
    psu1=0
    psu2=0
    #psudict={"PSU1":"Offline", "PSU2":"Offline"}
    send("STA")
    hexdata=getResponce()[4:]   #6a 
    intdata=int(hexdata, 16) #106
    bindata=bin(intdata)     #01101010

    if bindata[-3] == "1":
        #print("## SYS PSU[1]: InUse")
        psu1=1
        #psudict.update({"PSU1": "InUse"}) 
    if bindata[-2] == "1":
        #print("## SYS PSU[2]: InUse")
        psu2=1
        #psudict.update({"PSU2": "InUse"}) 

    psuhex=(str(psu1) + str(psu2)).zfill(8)
    print("## SYS PSU: " + str(psuhex))
    
    return psuhex
def checkPCMTemp():          #DEPRICATED
    send("TMP")
    #data=getResponce()[4:]
    #print("## TEMP PCM[X]: " + str(data) + "°c")
    data=(hex(int(getResponce()[4:]))[2:]).zfill(8)
    #data=hex(int(getResponce()[4:]))
    print("## TEMP PCM[X]: " + str(data))
    return data
def checkLoadedBaysComp():   #DEPRICATED
    baydict={1:False, 2:False, 3:False, 4:False}
    send("DP0")
    hexdata=getResponce()[4:]   
    intdata=int(hexdata, 16) 
    bindata=bin(intdata) 

    #                               #0     10011111 [9F] (DP0)
    if bindata[-1] != "1":          #1     10011110 [9E] (DP0)
        print("## HDD BAY[1]: InUse")    #       ^
        baydict.update({1: True})         #
    if bindata[-2] != "1":          #2     10011101 [9D] (DP0)
        print("## HDD BAY[2]: InUse")    #      ^
        baydict.update({2: True})         #
        bay2=1
    if bindata[-3] != "1":          #3     10011011 [9B] (DP0)
        print("## HDD BAY[3]: InUse")    #     ^
        baydict.update({3: True})         #
    if bindata[-4] != "1":          #4     10010111 [97] (DP0)
        print("## HDD BAY[4]: InUse")    #    ^
        baydict.update({4: True}) 
    return baydict                  
    #Pres  00010000 [10] (ISR)
    #   
def checkLoadedBays():       #DEPRICATED
    bay1=0
    bay2=0
    bay3=0
    bay4=0
    send("DP0")
    hexdata=getResponce()[4:]   
    intdata=int(hexdata, 16) 
    bindata=bin(intdata) 
    
    #                               #0     10011111 [9F] (DP0)
    if bindata[-1] != "1":          #1     10011110 [9E] (DP0)
        bay1=1                            #       ^
    if bindata[-2] != "1":          #2     10011101 [9D] (DP0)
        bay2=1                            #      ^
    if bindata[-3] != "1":          #3     10011011 [9B] (DP0)
        bay3=1                            #     ^
    if bindata[-4] != "1":          #4     10010111 [97] (DP0)
        bay4=1                            #    ^
    bayhex=(str(bay1) + str(bay2) + str(bay3) + str(bay4))
    print("## DRIVE BAYS: " + str(bayhex))

    return bayhex                  
    #Pres  00010000 [10] (ISR)
    #                                                        
def checkBacklightPer():     #DEPRICATED
    send("BKL")
    data=int(getResponce()[4:], 16)
    print("## Backlight State: " + str(data) + "%")
    return data

'''

''' Testing Funcs
while True:
    print("checking")
    if getInterupt() == True:
        result = getISR()
        if result == "UP":
            print(str(result) + " : " + str(upPushed))
        elif result == "USB":
            print(str(result) + " : " + str(usbPushed))
while True:
    send("ISR")
    print("\n=======")
    print(getResponce())
    time.sleep(0.5)
    count = count + 1
    val = hex(count)[2:]
    #print(str(val))
    send("IMR=" + str("9D"))   #00100000 on
    #print(getResponce())
while True:
                print("\n\n===========")
                print(tmpIsr)
                count = count + 1
                chkInput = SerialObj.readlines(1)
                print(chkInput)

                if chkInput == "":
                    pass
                elif count >= 100:
                    pass
                else:
                    pass
while True:
    #count += 1
    #print ("\n\n" + str(count) + "==========") 
    #print(getStatus())
    sig = handelSignal() 
    if sig == 1:
        print("Got ERR")
    elif sig == [b'']:           #01101010
        pass                     
    elif sig == [b'STA=2a\n']:   #00101010
        print("** Got DOWN **")  # ^   
    elif sig == [b'STA=4a\n']:   #01001010   #ISR=20 00010100
        print("** Got UP **")    #  ^   
    elif sig == [b'STA=62\n']:   #01100010   #ISR=08 00001000
        print("** Got EJECT **") #    ^
    elif sig == [b'STA=42\n']:
        print("** Got EJECT + UP **") #01101010


#           - Bit 0: No buttons pressed
    #       - Bit 1: Power adapter state changed on socket 2
    #       - Bit 2: Power adapter state changed on socket 1
    #       - Bit 3: USB copy button pressed
    #       - Bit 4: Drive presence changed
    #       - Bit 5: LCD up button pressed
    #       - Bit 6: LCD down button pressed
    #       - Bit 7: ??? (never observed as set)

    datain=getResponce()[4:]  #6a
    print(datain)
    print(type(datain)) 
    data1st=int(datain, 16)   #106
    print(data1st)
    print(type(data1st))
    data = bin(data1st)      #0b01101010
    print(data)
    print(type(data))  
    #data = bin(int(getResponce()[4:], 16))[2:].zfill(8) 
    print(data)
    print(type(data))  

'''