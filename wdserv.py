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

def checkForIncomingMail():
    global lstupdatetime, Alert
    try:
        file1 = open("daemon.txt", "r")
        f = file1.readlines()
        f2 = str(f[0]).rstrip('\n')
        file1.close()
        checklstupdatetime=str(f2)
        #print('Time was loaded [' + str(f2) + "]")
    except:
        f2=""
        checklstupdatetime=""
        #print('Time WAS NOT loaded correctly')

    if checklstupdatetime != lstupdatetime and checklstupdatetime:
        lstupdatetime = checklstupdatetime
        print("#################\ndata updated at [" + str(checklstupdatetime) + "], fetching...")
        try:
            file1 = open("daemon.txt", "r")
            f = file1.readlines() 
            vTime= str(f[0]).rstrip('\n')
            Hex = str(f[1]).rstrip('\n')    # RRRRLLTT BBLLKPDP  RPM,Level,temp,  Backlight,LED,Blink,Pulse,Drives,PSU
            Alert = str(f[2]).rstrip('\n')
            file1.close()
            lstvalue = str(Hex)
            print('# Following data was loaded: \n  [' + str(Hex) + "]\n  " + str(Alert) + "\n")
        except:
            f1=""
            #print('Data WAS NOT loaded')
        

        if Alert != "0":
            print("## BUTTON PUSHED! " + str(Alert) + "\n\n\n")

def sendOutgoingMail(led=False, lcd1=False, lcd2=False):
    with open('daemonin.txt', 'r') as file:
        data = file.readlines()
    file.close

    if led != False:
        ledsta=""
        backlight=led[0:2]
        ledstate=led[2:4]
        ledblk=led[5:]
        ledpulse=led[-1:]
        time.sleep(1)
        
        ledsta=(str(backlight) + str(ledstate) + str(ledblk) + str(ledpulse))

        data[0] = (str(ledsta) + "\n")
    else:
        data[0] =""


    if lcd1 != False:
        data[1] = (str(lcd1) + "\n")
    else:
        data[1] ="\n"
    if lcd2 != False:
        data[2] = (str(lcd2) + "\n")
    else:
        data[2] ="\n"

    data[3] = "O"

    with open('daemonin.txt', 'w') as file:
        file.writelines( data )
    file.close

    while True:
        time.sleep(2)
        with open('daemonin.txt', 'r') as file:
            data = file.readlines()
        file.close

        if data[3].rstrip('\r\n') == "ACK":
            data[3] = ("X\n")
            with open('daemonin.txt', 'w') as file:
                file.writelines( data )
            file.close
            return True
        else: 
            return False

    

###########################################################################
#############################  DUMMY  #####################################
###########################################################################
def dummyLoad():
  
    send("RPM")
    getResponce()
    #print(getResponce())
    time.sleep(1)
    send("RPM")
    getResponce()
    #print(getResponce())
    time.sleep(1)
    send("RPM")
    getResponce()
    #print(getResponce())
    time.sleep(1)
    send("BLK=00")
    #getResponce()
    #print(getResponce())
    #time.sleep(1)
    send("LED=1B")         #40- 01000000     #50- 01010000
    getResponce()
    #print(getResponce())
    time.sleep(1)

def dummyLoad2():
    time.sleep(1)

###########################################################################
#############################   MAIN   ####################################
###########################################################################
time.sleep(1)

vled="320200"
vlcd1="Test"
vlcd2="Transmission"
MailToSend=True

while True:
    #dummyLoad2()

    checkForIncomingMail()
    if MailToSend ==True:
        did=sendOutgoingMail(vled, vlcd1, vlcd2)
        if did == True:
            MailToSend=False
            print("It Did Do")
        else:
            print("Failed")
    
    

    
SerialObj.close()          # Close the port








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