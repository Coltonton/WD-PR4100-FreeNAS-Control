#### sudo /mnt/pool/py/bin/python3 /home/admin/wddhw/wdbackserver.py

import serial
import time
from datetime import datetime as clock
import json



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

LastSavedDataByte1="00000000"
LastSavedDataByte2="00000000"
alert=False
AlertByte="0"
laststa="0"
ProgramHealth=""
backendState="Offline"





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
    print("get init")
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
    ans = SerialObj.readline().decode().strip()
    SerialObj.flushInput()
    
def getResponce():
    ans = SerialObj.readline().decode().strip()
    SerialObj.flushInput()
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
    outdata="0"
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
    makedatabyte1    = ""                                                                   #         Fan RPM[R] ____/    \____ Fan Level[L] (%)  
    isrbyte     = 0 
    dprint("", dbgd, tme=True)
    global laststa

    #Get Value for each DataSource (RPM,FAN,TEMP(TMP))
    for x in tochecklist:
        send(x)                           # Ask For State
        #print(x)
        tmpvar = str(getResponce())#[4:])  # Get Responce
        if tmpvar == "ALERT":
            print("ALERT1")
            #send("STA")
            #laststa=getResponce()
            #print(laststa)
            send(x)
            tmpvar2=getResponce()[4:]
            #print(tmpvar2)
        elif tmpvar[0:3] == "ISR":
            if int(tmpvar[4:]) > 0:
                isrbyte=int(tmpvar[4:])
                print("GOT AN ISR OF [" + str(isrbyte) + "] in DataByte1")
            else:
                isrbyte=0
            send(x)
            tmpvar = str(getResponce())#[4:])  # Get Responce
            tmpvar2 = tmpvar[4:]
        else:
            tmpvar2 = tmpvar[4:]
        makedatabyte1 += tmpvar2              # Add it to our 8 Byte Value
        dlist = dlist + [ x , "[", tmpvar, "]" +"\n‡ "] # Add for debug output
    
    #DebugPrint Statment
    dprint(dlist, dbgd, tme=False, eod=False)     # Print the debug info
    dprint(makedatabyte1, dbgd, tme=False, eod=False)  # Print the full 8 byte value
    dprint("", dbgd, tme=False, eod=True)         # End Debug print

    #print(type(makedatabyte1))
    return makedatabyte1#,isrbyte

def pullDataByte2():      # Get LED State,Blinking,Pulsing  and Backlight Level -             Returns 8 byte value 0x BBLLKPXX ex. b'641b0000
    tochecklist = ["BKL", "LED", "BLK", "PLS"]                                                #                       \/\/||\/
    dlist       = ["Called pullDataByte2() Part[Lights]", "\n‡ "]                             # BackLight Level[B] ___/ / |\ \___ Unassigned[X]
    lighthex    = ""                                                                          #       Led State[L] ____/  | \____ Led Pulse[P]
    dprint("", dbgd, tme=True)                                                                #                      Led Blink[K]

    for x in tochecklist:
        send(x)                           # Ask For State
        tempvar = str(getResponce())#[4:])  # Get Responce
        if tempvar == "ALERT":
            print("ALERT2")
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

    dlist2       = ["Called pullDataByte2() Part[HW]", "\n‡ "]                              #                       ||\\\///
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
    global ProgramHealth
    with open('daemonin.txt', 'r') as filein: datain = filein.readlines()
    filein.close

    if datain[0].rstrip('\r\n') == "ONLINE" and ProgramHealth != "ONLINE":
        print("PROGRAM STATUS: [ONLINE]")
        programOnline()
        ProgramHealth="ONLINE"

    if datain[0].rstrip('\r\n') == "OFFLINE" and ProgramHealth != "OFFLINE":
        print("PROGRAM STATUS: [OFFLINE]")
        programOffline()
        ProgramHealth="OFFLINE"

    if datain[1].rstrip('\r\n') == "CMD" or datain[1].rstrip('\r\n') == "LST":
        sendlst=[]
        issuccess=[]

        if datain[1].rstrip('\r\n') == "CMD":
            sendlst.append(datain[2].rstrip('\r\n'))
        elif datain[1].rstrip('\r\n') == "LST":
            sendlsttxt=datain[2].rstrip('\r\n')
            sendlsttxt = sendlsttxt.replace("'", '"')
            sendlst = json.loads(sendlsttxt)

        for item in sendlst:
            while True:
                if datain[2] == "\n":
                    break
                send(item)
                resp = getResponce()
                print("\n" + resp + ": " + item)
                if resp == "ACK":
                    issuccess.append("ACK")
                    break

        datain[1] = ("ACK\n")
        with open('daemonin.txt', 'w') as fileout: fileout.writelines( datain )
        fileout.close

        SerialObj.flushInput()

        

def programHealthCheck(datain=[]):
    global ProgramHealth
    #if datain == []:
    with open('daemonin.txt', 'r') as filein:
        datain = filein.readlines()
    filein.close

    if datain[0].rstrip('\r\n') == "ONLINE" and ProgramHealth != "ONLINE":
        print("PROGRAM STATUS: [ONLINE]")
        print("Please wait for handshake to complete...\n")
        programOnline()
        ProgramHealth="ONLINE"

    if datain[0].rstrip('\r\n') == "OFFLINE" and ProgramHealth != "OFFLINE":
        print("PROGRAM STATUS: [OFFLINE]")
        ProgramHealth="OFFLINE"
    

def checkdriveRemoved():
    pass
#ISR=10 = Drive Removed/Added
#

def bkndServOnline(starting=False):
    time.sleep(1)
    send("BKL=64")
    send("LED=06")
    if starting==False:
        time.sleep(1)
        send("BLK=00")
        time.sleep(1)
        send("LN1= Server Online")
        time.sleep(.5)
        send("LN2=Program ????????")
        time.sleep(.5)
        send("FAN=32")
        time.sleep(1)

        with open('daemon.txt', 'r') as file1:
            data = file1.readlines()
        file1.close
                    
        data[0] = "ONLINE\n"
        data[1] = str(clock.now().strftime("%m/%d %I:%M.%S\n"))
        data[2] = "\n" 
        data[3] = "\n"
                    
        with open('daemon.txt', 'w') as file1:
            file1.writelines( data )
        file1.close
        
        print("Backend Server Status: [UP]")


    else:
        time.sleep(.1)
        send("BLK=06")
        time.sleep(.1)
        send("LN1= Server Starting")
        time.sleep(.1)
        send("LN2=Program ##########")
        send("FAN=64")
        print("Backend Server Status: [STARTING]")

def bkndServOffline():
    time.sleep(1)
    send("BKL=64")
    time.sleep(.1)
    send("PLS=00")
    time.sleep(.5)
    send("LED=02")
    time.sleep(.5)
    #send("BLK=01") led = 03
    send("BLK=02")
    time.sleep(.5)
    send("FAN=64")
    time.sleep(.1)
    send("LN1= Server Offline")
    time.sleep(.1)
    send("LN2=Program ????????")


    with open('daemon.txt', 'r') as file1:
        data = file1.readlines()
    file1.close

    data[0] = "OFFLINE\n"
                
    with open('daemon.txt', 'w') as file1:
        file1.writelines( data )
    file1.close
    
def servOnline(starting=False):
    time.sleep(1)
    send("BKL=64")
    send("LED=01")
    time.sleep(1)
    send("BLK=00")
    time.sleep(1)
    send("LN1= Server Online")
    time.sleep(.1)
    send("LN2= Waiting 4 Prog")
    time.sleep(1)
    print("Main Server Status: [UP]")

def programOnline():
    time.sleep(1)
    send("LN1= Server Online")
    time.sleep(.1)
    send("LN2=Program Online")
    time.sleep(.1)
    send("BLK=00")
    time.sleep(.1)
    #send("LED=04")
    #time.sleep(.1)
    #send("PLS=04")
    #time.sleep(1)
    #sendEmpty()

def programOffline():
    time.sleep(.5)
    send("LN1= Server Online")
    res=getResponce()
    time.sleep(.1)
    send("LN2=Program Offline")
    time.sleep(.1)
    send("LED=06")
    res=getResponce()
    time.sleep(.1)
    send("BLK=06")
    res=getResponce()
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
def execute_app():
    global alert
    global AlertByte
    global laststa
    global LastSavedDataByte1
    global LastSavedDataByte2
    global ProgramHealth
    WaitingOnProgram = False

    bkndServOnline(True)
    time.sleep(1)
    sendEmpty()
    getInit()
    bkndServOnline()
    time.sleep(1)
    sendEmpty()
    programHealthCheck()

    # MAIN LOOP
    while True:
        # If the main source program is ONLINE     
        if ProgramHealth == "ONLINE":
            WaitingOnProgram = False
            returnedDataByte1=pullDataByte1()
            returnedDataByte2=pullDataByte2()
            AlertByte=str(getISR())
            getIncomingMail()
            #ledSend=getIncomingMail()[0]
            #Lcd1Send=getIncomingMail()[1]
            #Lcd2Send=getIncomingMail()[2]
            time.sleep(1)

            # If an ALERT condition arises
            #if alert == True:
                #print(laststa)
                #AlertByte=laststa
                #alert=False
                #pass 

            #Check if Values differ from saved or ALERT
            if (str(returnedDataByte1) != str(LastSavedDataByte1)) or (str(returnedDataByte2) != str(LastSavedDataByte2)) or str(AlertByte) != "0": 
                # Verify/Try And see if databyte1 returned a valid response 
                try:
                    tempvar=int(returnedDataByte1[6:])
                # If ValueError (most likely) Say the Responce was invalid and try again
                except ValueError: 
                    dbgmsg="DataByte1 Provided an invalid response [" + returnedDataByte1 + "]"
                    dprint(dbgmsg, dbgd, tme=True, eod=True)
                # Some Other Exception Occured
                except:  
                    dbgmsg="DataByte1 Provided an invalid response [" + returnedDataByte1 + "]"
                    dprint("DataByte1  - UnknownException", dbgd, tme=True, eod=True)
                # Everything looks A-OK go ahead and process
                else:    
                    lowval = int(LastSavedDataByte1[6:]) - 2  # Privious temp minus 2
                    hihval = int(LastSavedDataByte1[6:]) + 2  # Privious temp plus 2
                    #print(LastSavedDataByte1, lowval, hihval, AlertByte)
                    #print(str(tempvar) + "vs" + str(LastSavedDataByte1[6:] ) )

                    # We only check if temp has changed by +/- 2 degrees as RPM and Fan level are not really crucial to update on OR there is an alert
                    if (int(tempvar) >= hihval) or (int(tempvar) <= lowval) or str(AlertByte) != "0":
                        LastSavedDataByte1 = str(returnedDataByte1) # Save the new DataByte1 value to the register
                        LastSavedDataByte2 = str(returnedDataByte2) # Save the new DataByte2 value to the register

                        # Read the Output file
                        with open('daemon.txt', 'r') as f: filedata = f.readlines()
                        f.close
                        
                        # Create the data for the output file 
                        filedata[0] = "ONLINE\n"                                      # Backend Health Status
                        filedata[1] = str(clock.now().strftime("%m/%d %I:%M.%S\n"))   # Last Update Time
                        filedata[2] = (str(returnedDataByte1) + str(returnedDataByte2) + "\n") # Data Output
                        filedata[3] = str(AlertByte) + "\n"                           # Alert Output
                            

                        print(filedata)
                        # Write the new data to the output file
                        with open('daemon.txt', 'w') as f: f.writelines( filedata )
                        f.close
                        AlertByte = "0"   #Clear AlertByte

        # If the main source program is OFFLINE          
        else:
            # If this is the first loop when the main source program is OFFLINE show the "program offfline" message and set WaitingOnProgram
            if (WaitingOnProgram == False ):
                programOffline()
                print("Waiting For Program To Come Online...")
                WaitingOnProgram = True
                
            #update the status of the main source program and wait 5 seconds
            programHealthCheck()
            time.sleep(5)       

def main():
    try:
        execute_app()
    finally:
        bkndServOffline()

if __name__=='__main__':
    main()


# EXAMPLE OUTPUT
# ONLINE             <-BackendServerStatus
# 10/08 11:26.29     <-Last Update Time
# 03de3223640600C2   <-Data Output (see note)
# 0                  <-Alert Output


#NOTE: Data Output 
# 03de3223640600C2
# |______||______|
#    ||      ||
#    ||  databyte2
# databyte1


#NOTE: Databyte1
''' ex 03de 32  23
        ||  ||  ||
       RPM  FAN Temp '''

#NOTE: Databyte2
'''

'''










#    filein = open("daemonin.txt", "w")
    #    filein.seek(0)
    #    file1.write(str(clock.now().strftime("%m/%d %I:%M.%S\n")) + str(LastSavedDataByte1) + str(LastSavedDataByte2) + "\n" + str(AlertByte) )
    #    print(str(LastSavedDataByte1) + "\n" + str(byte2) + "\n" + str(AlertByte) + "\n" )
    #    file1.close
    #    alert=False

    #if alert == True:
    #    print("uh alert?")
    #    file1 = open("daemon.txt", "w")
    #    file1.seek(0)
    #    file1.write(str(clock.now().strftime("%m/%d %I:%M.%S\n")) + str(LastSavedDataByte1) + str(LastSavedDataByte2) + "\n" + str(AlertByte) )
    #    print(str(LastSavedDataByte1) + "\n" + str(byte2) + "\n" + str(AlertByte) + "\n" )
    #    file1.close
    #    alert=False