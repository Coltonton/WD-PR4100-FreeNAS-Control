#### sudo /mnt/pool/py/bin/python3 /home/admin/wddhw/wdbackserver.py

import serial
import time
from datetime import datetime as clock



###########################################################################
#############################   VARS   ####################################
###########################################################################
SerialObj = serial.Serial('/dev/ttyS2') # ttyUSBx format on Linux
SerialObj.baudrate = 9600  # set Baud rate to 9600
SerialObj.bytesize = 8   # Number of data bits = 8
SerialObj.parity  ='N'   # No parity
SerialObj.stopbits = 1   # Number of Stop bits = 1
terminator = b'\r'
upPushed = False
usbPushed = False
downPushed = False

lastsent1="00000000"
lastsent2="00000000"
alert=False
AlertByte="0"
laststa="0"




dbgn = "none"
dbgi = "info"
dbgd = "debug"
dbga = "all"
debugPrint="none"


###########################################################################
#############################   FUNCS   ###################################
###########################################################################
def dprint(pnt="", lvl=dbgn, tme=True, eod=False):   #Debug printing   pass in dbgn for none - dbgi for info - dbgd for debug and dbga for all
    if debugPrint != "none" :
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

def getInit():
    send("VER")
    print(getResponce())
    send("CFG")
    print(getResponce())
    send("STA") 
    print(getResponce())
    send("IMR=ff")   #00100000 on
    print(getResponce())
    send("ISR")
    print(getResponce())
    send("FAN=64")
    print(getResponce())

def send(var):
    write_place  = (var).encode()
    SerialObj.write(write_place + terminator)

def sendEmpty():
    #print("Sending Empty...")
    SerialObj.write(terminator)
    
def getResponce():
    
    ans = SerialObj.readline().decode().strip()
    #SerialObj.flushInput()
    #sprint("ans is:")
    #print(ans)
    if ans == "ALERT":
        data = getISR()
        if data == "BTTN_UP" or "BTTN_DOWN":
            checkIfButtons(data)
        #print(data)
        #ans = data
    #lif ans == "\rISR=0\n":
    #    print ("booo")
        #ans = ""
    #elif ans == "\rSTA=6a\n":
        #ans = ""
    #return ans
    return ans

def getStatus():
    tmpVar = []
    SerialObj.flushInput()
    SerialObj.write(b'STA\r')
    tmpVar.append(SerialObj.readline())#s(15)#.decode() .
    #print(tmpVar)
    if tmpVar == [b'STA=6a\n']:
        #0print("responce is: ")
        #print(tmpVar)
        #print("end data responce")
        tmpVar = [b'']
    else:
        return tmpVar
    
def getISR():
    global upPushed
    global usbPushed
    global downPushed
    btn=""
    outdata=""
    SerialObj.flushInput()
    #print("writing isr")
    SerialObj.write(b'ISR\r')
    while True:
        tmpIsr = SerialObj.readlines(1)
        tmpIsr = tmpIsr[0].decode().strip()
        ##print(tmpIsr) 
        if (SerialObj.in_waiting.bit_length() == 1):    #Buttons
            if tmpIsr == "ISR=08" or "ISR=20" or "ISR=40":
                SerialObj.write(b'ISR\r')
                SerialObj.flushInput()
                break  
            elif tmpIsr == "ISR=02" or "ISR=04":    #PSU's
                SerialObj.write(b'ISR\r')
                SerialObj.flushInput()
                break  
            elif tmpIsr == "ISR=10":    #Drive Change's
                SerialObj.write(b'ISR\r')
                SerialObj.flushInput()
                break  
            else:
                tmpIsr = SerialObj.readline().decode()
    tmpIsr = tmpIsr[4:]


    # Buttons
    if tmpIsr == "20":
        if upPushed == False:
            upPushed = True
        else:
            upPushed = False
        outdata="BTTN_UP"
    elif tmpIsr == "40": 
        if downPushed == False:
            downPushed = True
        else:
            downPushed = False
        outdata="BTTN_DOWN"
    elif tmpIsr == "08":
        if usbPushed == False:
            usbPushed=True
        else:
            usbPushed=False
        outdata="BTTN_USB"
    
    # PSUs
    if tmpIsr == "02":
        outdata="PSU_2"
    elif tmpIsr == "04": 
        outdata="PSU_1"

    # Drive Presence
    if tmpIsr == "10":
        #Pres  00010000 [10] (ISR)
        #         ^                
        print("DRIVE ADDED/REMOVED")
        outdata="Drive_Presence"

    #print("Returning: " + str(outdata))
    return outdata

def getInterupt():
    ans = SerialObj.readlines(1)
    #SerialObj.readall()
    if ans == [b'\rALERT\n']:
        SerialObj.flushInput()
        return 1
    elif ans == b'\rERR\n':
        return 1
    else:
        return 0

def handelSignal():
    ans = SerialObj.readline().decode()
    if ans == "\rALERT\n":
        return getStatus()
    elif ans == "\rERR\n":
        return 1


def checkIfButtons(data=False):
    global laststa, alert
    if data == False:
        data = getISR()
    #print(data)
    if data == "BTTN_UP":
        print("## BUTTON PUSHED!: " + str(data))
        laststa = 1
        alert = True
    elif data == "BTTN_DOWN":
        print("## BUTTON PUSHED!: " + str(data))
        laststa = 2
        alert = True
    elif data == "BTTN_USB":
        print("## BUTTON PUSHED!: " + str(data))
        laststa = 4
        alert = True
    return data


def checkLights():      # Get LED State,Blinking,Pulsing  and Backlight Level -             Returns 8 byte value 0x BBLLKPXX ex. b'641b0000
    tochecklist = ["BKL", "LED", "BLK", "PLS"]                                              #                       \/\/||\/
    dlist       = ["Called checkLights()", "\n‡ "]                                          # BackLight Level[B] ___/ / |\ \___ Unassigned[X]
    lighthex    = ""                                                                        #       Led State[L] ____/  | \____ Led Pulse[P]
    dprint("", dbgd, tme=True)                                                              #                      Led Blink[K]

    for x in tochecklist:
        send(x)                           # Ask For State
        tempvar = str(getResponce()[4:])  # Get Responce
        if x == "BLK" or "PLS":
            lighthex += tempvar
        else:
            lighthex += tempvar               # Add it to our 8 Byte Value
        dlist = dlist + [ x , "[", tempvar, "]" +"\n‡ "] # Add for debug output
    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(lighthex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print

    return lighthex

def checkThermals():    # Get Fan RPM, Speed, and PCM Temp -                                Returns 8 byte value 0x RRRRLLTT ex. b'06AE6418
    tochecklist = ["RPM", "FAN", "TMP"]                                                     #                       \\//\/\/
    dlist       = ["Called checkThermals()", "\n‡ "]                                        #                        \/  \ \___ PCM Temp[T]  (°C)
    thermhex    = ""                                                                        #         Fan RPM[R] ____/    \____ Fan Level[L] (%)   
    dprint("", dbgd, tme=True)

    for x in tochecklist:
        send(x)                           # Ask For State
        tempvar = str(getResponce()[4:])  # Get Responce
        thermhex += tempvar               # Add it to our 8 Byte Value
        dlist = dlist + [ x , "[", tempvar, "]" +"\n‡ "] # Add for debug output
    
    #DebugPrint Statment
    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(thermhex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print

    return thermhex

def checkHWConnections():  # Get PSU Online status, drivebays loaded, Speed, and PCM Temp - Returns 8 byte value 0x BPXXXXXX ex. b'C2000000
    dlist       = ["Called checkHWConnections()", "\n‡ "]                                   #                       ||\\\///
    psu=0                                                                                   #  Occupied Bays[B] ___/ | \\//
    bay=0                                                                                   #     PSU Status[P] ____/   \/
    dprint("", dbgd, tme=True)                                                              #     Unassigned[X] ________/ 

    if True:
        retvar=""
        send("DP0")
        retvar=getResponce()
        #resp=getResponce()[4:]
        #print(retvar)
        if retvar == "ALERT":
            send("DP0")
            retvar=getResponce()
            print(retvar)
        retvar = retvar[4:]
        baybin=(bin(int((retvar), 16))[6:].zfill(4)) #0011
        #                              #0     00001111 [9F] (DP0)
        if baybin[-1] != "1":          #1     00001110 [9E] (DP0)
            bay = bay+1                      #       ^
        if baybin[-2] != "1":          #2     10011101 [9D] (DP0)
            bay = bay+2                      #      ^
        if baybin[-3] != "1":          #3     00001011 [9B] (DP0)
            bay = bay+4                      #     ^
        if baybin[-4] != "1":          #4     00000111 [97] (DP0)
            bay = bay+8                      #    ^
        bayhex=hex(bay)[2:].capitalize()
        dlist = dlist + ["BAY[", bayhex, "]" +"\n‡ "] # Add for debug output

    if True:
        send("STA") 
        hexdata=getResponce()[4:]   #6a 
        intdata=int(hexdata, 16) #106
        bindata=bin(intdata)     #01101010
        #
        if bindata[-3] == "1":
            psu=psu+1
        if bindata[-2] == "1":
            psu=psu+2
        psuhex=hex(psu)[2:]
        dlist = dlist + ["PSU[", psuhex, "]" +"\n‡ "] # Add for debug output
    
    hwhex=((str(bayhex)) + str(psuhex) + "000000")
    

    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(hwhex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print
    #print("## HW CONNS: " + str(hwhex))

    return hwhex                  

def pullDataByte1():    # Get Fan RPM, Speed, and PCM Temp -                                Returns 8 byte value 0x RRRRLLTT ex. b'06AE6418
    tochecklist = ["RPM", "FAN", "TMP"]                                                     #                       \\//\/\/
    dlist       = ["Called checkThermals()", "\n‡ "]                                        #                        \/  \ \___ PCM Temp[T]  (°C)
    thermhex    = ""                                                                        #         Fan RPM[R] ____/    \____ Fan Level[L] (%)   
    dprint("", dbgd, tme=True)
    tmpvar=""
    tmpvar2=""
    global laststa

    for x in tochecklist:
        send(x)                           # Ask For State
        tmpvar = str(getResponce())#[4:])  # Get Responce
        if tmpvar == "ALERT":
            #send("STA")
            #laststa=getResponce()
            #print(laststa)
            send(x)
            tmpvar2=getResponce()[4:]
            #print(tmpvar2)
        else:
            tmpvar2 = tmpvar[4:]
        thermhex += tmpvar2              # Add it to our 8 Byte Value
        dlist = dlist + [ x , "[", tmpvar, "]" +"\n‡ "] # Add for debug output
    
    #DebugPrint Statment
    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(thermhex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print

    #print(type(thermhex))
    #print(thermhex)
    return thermhex

def pullDataByte2():      # Get LED State,Blinking,Pulsing  and Backlight Level -             Returns 8 byte value 0x BBLLKPXX ex. b'641b0000
    tochecklist = ["BKL", "LED", "BLK", "PLS"]                                                #                       \/\/||\/
    dlist       = ["Called pullDataByte2() Part[Lights]", "\n‡ "]                                            # BackLight Level[B] ___/ / |\ \___ Unassigned[X]
    lighthex    = ""                                                                          #       Led State[L] ____/  | \____ Led Pulse[P]
    dprint("", dbgd, tme=True)                                                                #                      Led Blink[K]

    for x in tochecklist:
        send(x)                           # Ask For State
        tempvar = str(getResponce())#[4:])  # Get Responce
        if tempvar == "ALERT":
            send(x)                           # Ask For State
            tempvar = str(getResponce())[4:]  # Get Responce
        else:
            tempvar = tempvar[4:]
            
        if x in ["BLK", "PLS"]:
            tmpvar2 = tempvar[1:]               # Add it to our 8 Byte Value
        else:
            tmpvar2 = tempvar               # Add it to our 8 Byte Value
        lighthex += tmpvar2
                
        
        dlist = dlist + [ x , "[", tmpvar2, "]" +"\n‡ "] # Add for debug output
    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(lighthex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print

    dlist2       = ["Called pullDataByte2() Part[HW]", "\n‡ "]                                   #                       ||\\\///
    psu=0                                                                                   #  Occupied Bays[B] ___/ | \\//
    bay=0                                                                                   #     PSU Status[P] ____/   \/
    dprint("", dbgd, tme=True)                                                              #     Unassigned[X] ________/ 

    if True:
        retvar=""
        send("DP0")
        retvar=getResponce()
        if retvar == "ALERT":
            send("DP0")
            retvar=getResponce()
            print(retvar)
        retvar = retvar[4:]
        baybin=(bin(int((retvar), 16))[6:].zfill(4)) #0011
        #                              #0     00001111 [9F] (DP0)
        if baybin[-1] != "1":          #1     00001110 [9E] (DP0)
            bay = bay+1                      #       ^
        if baybin[-2] != "1":          #2     10011101 [9D] (DP0)
            bay = bay+2                      #      ^
        if baybin[-3] != "1":          #3     00001011 [9B] (DP0)
            bay = bay+4                      #     ^
        if baybin[-4] != "1":          #4     00000111 [97] (DP0)
            bay = bay+8                      #    ^
        bayhex=hex(bay)[2:].capitalize()
        dlist2 = dlist2 + ["BAY[", bayhex, "]" +"\n‡ "] # Add for debug output

    if True:
        send("STA") 
        retvar=getResponce()
        if retvar == "ALERT":
            send("STA")
            retvar=getResponce()
            print(retvar)
        retvar = retvar[4:]
        bindata=bin(int(retvar, 16))[4:]   #01101010
        #
        if bindata[-3] == "1":
            psu=psu+1
        if bindata[-2] == "1":
            psu=psu+2
        psuhex=hex(psu)[2:]
        dlist2 = dlist2 + ["PSU[", psuhex, "]" +"\n‡ "] # Add for debug output
    
    hwhex=((str(lighthex) + str(bayhex)) + str(psuhex))
    

    dprint(dlist2, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(hwhex, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print
    #print("## HW CONNS: " + str(hwhex))

    
    return hwhex                


def getIncomingMail():
    with open('daemonin.txt', 'r') as filein:
        datain = filein.readlines()
    filein.close

    if datain[3].rstrip('\r\n') == "O":
        print("getincomingmail")
        leddatain=datain[0]
        send("BKL=" + str(leddatain[0:2]))
        bklack = str(getResponce()) # Get Responce
        send("LED=" + str(leddatain[2:4]))
        ledack = str(getResponce()) # Get Responce
        send("BLK=" + str(leddatain[4:5]))
        plsack = str(getResponce()) # Get Responce
        send("PLS=" + str(leddatain[5:].rstrip('\n')))
        plsack = str(getResponce()) # Get Responce
        #print(("uhh    " + " bl" + str(backlight) + " s" + str(ledstate) + " b" + str(ledblk) + " p" + str(ledpulse)))

        #time.sleep(1)
        send("LN1=" + str(datain[1].rstrip('\n')))
        ln1ack = str(getResponce()) # Get Responce
        #time.sleep(1)
        send("LN2=" + str(datain[2].rstrip('\n')))
        ln2ack = str(getResponce()) # Get Responce

        datain[3] = ("ACK\n")
        with open('daemonin.txt', 'w') as file:
            file.writelines( datain )
        file.close

        SerialObj.flushInput()
        print("returning from get mail")

def checkdriveRemoved():
    pass
#ISR=10 = Drive Removed/Added
#


###########################################################################
#############################  DUMMY  #####################################
###########################################################################
def allprintoutput(lte, the, hdw):
    dprint("", dbgi, tme=True)
    dlist = ["Output Bytes", "\n‡ "]
    dlist = dlist + ["LEDS:            0x", str(lte), " [BBLLKPXX]", "\n‡ "]  # 0xBBLLKPXX - [BB]Backlight     [LL]LEDs State  [K]Blink [P]Pulse   [XX] RESERVED 
    dlist = dlist + ["Thermals:        0x", str(the), " [RRRRLLTT]", "\n‡ "]  # 0xRRRRLLTT - [RRRR]Fan RPM     [LL]Fan Level   [TT]PCM Temp
    dlist = dlist + ["HW Connections:  0x", str(hdw), " [BPXXXXXX]", "\n"]  # 0xBPXXXXXX - [B]Occupied Bays  [P]PSU Status  [XXXXXX]RESERVED
    #DebugPrint Statment
    dprint(dlist, dbgi, tme=False, eod=False)     # Print the debug info
    dprint("", dbgi, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgi, tme=False, eod=True)         # End Debug print

###########################################################################
#############################   MAIN   ####################################
###########################################################################
time.sleep(1)
sendEmpty()
getInit()

while True:
    byte1=pullDataByte1()
    byte2=pullDataByte2()

    getIncomingMail()
    #ledSend=getIncomingMail()[0]
    #Lcd1Send=getIncomingMail()[1]
    #Lcd2Send=getIncomingMail()[2]
    #AlertByte=laststa

    time.sleep(1)

    if alert == True:
        #print("uh alert?")
        AlertByte=laststa
        print(AlertByte)
        alert=False 

    if (str(byte1) != str(lastsent1)) or (str(byte2) != str(lastsent2)) or AlertByte != "0":
        #print(byte1)
        tmpvar=int(byte1[6:])
        #print(str(tmpvar) + "vs" + str(lastsent1[6:] ) )
        lowval = int(lastsent1[6:]) - 2
        hihval = int(lastsent1[6:]) + 2
        if (int(tmpvar) >= hihval) or (int(tmpvar) <= lowval) or AlertByte != "0":# or (int(tmpvar) <= (int(lastsent1[6:]) - 2)):
            lastsent1 = str(byte1)
            lastsent2 = str(byte2)
            #allprintoutput(LightsHex, ThermalsHex, HwConnectHex)
            #print("Writing to file")

            with open('daemon.txt', 'r') as file1:
                data = file1.readlines()
            file1.close
            
            data[0] = str(clock.now().strftime("%m/%d %I:%M.%S\n"))
            data[1] = (str(byte1) + str(byte2) + "\n")
            data[2] = str(AlertByte) + "\n"
            

            with open('daemon.txt', 'w') as file1:
                file1.writelines( data )
            file1.close

            AlertByte = "0"

            #file1 = open("daemon.txt", "w")
            #file1.seek(0)

            #file1.write(str(clock.now().strftime("%m/%d %I:%M.%S\n")) + str(byte1) + str(byte2) + "\n" )
            print(data)
 

    
SerialObj.close()          # Close the port





#    filein = open("daemonin.txt", "w")
    #    filein.seek(0)
    #    file1.write(str(clock.now().strftime("%m/%d %I:%M.%S\n")) + str(lastsent1) + str(lastsent2) + "\n" + str(AlertByte) )
    #    print(str(lastsent1) + "\n" + str(byte2) + "\n" + str(AlertByte) + "\n" )
    #    file1.close
    #    alert=False

    #if alert == True:
    #    print("uh alert?")
    #    file1 = open("daemon.txt", "w")
    #    file1.seek(0)
    #    file1.write(str(clock.now().strftime("%m/%d %I:%M.%S\n")) + str(lastsent1) + str(lastsent2) + "\n" + str(AlertByte) )
    #    print(str(lastsent1) + "\n" + str(byte2) + "\n" + str(AlertByte) + "\n" )
    #    file1.close
    #    alert=False