#### /mnt/pool/py/bin/python3 /home/admin/wddhw/wdserv.py
import time
from datetime import datetime as clock
import socket



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
ProgramHealth=""
backendState="OFFLINE"
Handshake=False

dbgn = "none"
dbgi = "info"
dbgd = "debug"
dbga = "all"
debugPrint="all"
btnD="BTTN_DOWN"
btnU="BTTN_UP"
btnH="BTTN_USB"


WDRPM=""
WDFAN=""
WDTEMP=""
WDBACKLIGHT=""
WDLED=""
WDBLINK=""
WDLEDPULSE=""
WDDRiVE=""
WDALERT=""

userBacklightTimeout=5
userBacklightDIM=25
userBacklightBRIGHT=100
userLedColor="04"
userLedPulseOnInactive=True

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

def backendHealthCheck():       #Function to read the status of the backend server daemon
    global backendState

    # Read the Daemon File
    with open('daemon.txt', 'r') as filein: datain = filein.readlines()
    filein.close()

    # Get Daemon status and do what must be done.
    Status = str(datain[0]).rstrip('\n')
    if Status == "OFFLINE":
        backendState="OFFLINE"
        time.sleep(1)
        return backendState
    elif Status == "ONLINE":
        backendState="ONLINE"
        time.sleep(1)
        return backendState
    else:
        return "Error"

def checkForIncomingMail():
    global lstupdatetime, WDALERT
    try:   # See if timestamp is there
        with open('daemon.txt', 'r') as filein: datain = filein.readlines()
        filein.close
        f2 = str(datain[1]).rstrip('\n')
        checklstupdatetime=str(f2)
    except: # Timestamp finding had an error
        f2=""
        checklstupdatetime=""

    # If reading the file results in the backend server being OFFLINE
    if str(datain[0]).rstrip('\n') == "OFFLINE":
        print("WARNING BACKEND SERVER WENT/IS OFFLINE, Terminating...")
        backendState="OFFLINE"
        return

    if checklstupdatetime != lstupdatetime and checklstupdatetime:
        lstupdatetime = checklstupdatetime
        print("\n#################\ndata updated at [" + str(checklstupdatetime) + "], fetching...")
        try:
            file1 = open("daemon.txt", "r")
            f = file1.readlines() 
            Status = str(f[0]).rstrip('\n')
            vTime  = str(f[1]).rstrip('\n')
            Hex    = str(f[2]).rstrip('\n')    # RRRRLLTT BBLLKPDP  RPM,Level,temp,  Backlight,LED,Blink,Pulse,Drives,PSU
            WDALERT  = str(f[3]).rstrip('\n')
            file1.close()
            lstvalue = str(Hex)
            print('#[' + str(Hex) + "]\n  " + str(Alert) + "\n")

            #return Status, vTime, Hex, Alert
            decodeData(Hex)
        except:
            f1=""
        
        if Alert == "1":
            print("## BUTTON PUSHED! " + str(Alert) + "\n\n\n")

def Send(datatosend):           # Call this function to send data to the backend server daemon which then sends the WD faceplate. Pass in a STR ot List   
    # Read the file
    with open('daemonin.txt', 'r') as filein: data = filein.readlines()
    filein.close

    # If the user provides a list
    if type(datatosend) == list:
        senddata = "ONLINE\nLST\n" + str(datatosend)
        print("Sending List: " + str(datatosend))
    else: # If the user provides a string
        senddata = "ONLINE\nCMD\n" + datatosend
        print("Sending: " + str(datatosend))

    # Write the data to the file
    with open('daemonin.txt', 'w') as f: f.writelines( senddata )
    f.close

    i=0
    while True:
        # Wait and read the backend server daemon file
        time.sleep(1)
        with open('daemonin.txt', 'r') as f: data = f.readlines()
        f.close

        # Check the backend server daemon responded with an ACK (acknowledge)
        if data[1].rstrip('\r\n') == "ACK":
            i=0
            datav = "ONLINE\nXXX\n"  # Clear the command identifier
            with open('daemonin.txt', 'w') as fileout: fileout.writelines( datav ) # Write the cleared command identifier
            fileout.close
            print("ACK\n")
            return True
        else: # If not get an acknowledgement count here 5 times (seconds) then return False if command failed
            i = i + 1
            if i > 5:
                print("Server Did not respond in 5 seconds...\n")
                checkForIncomingMail()
                i=0
                #return False
            time.sleep(1)

def decodeData(data2decode):    # This function takes out data and converts it into variables
    WDRPM=data2decode[0:4]
    WDFAN=data2decode[4:6]
    WDTEMP=data2decode[6:8]
    WDBACKLIGHT=data2decode[8:10]
    WDLED=data2decode[10:12]
    WDBLINK=data2decode[12:13]
    WDLEDPULSE=data2decode[13:14]
    WDDRiVE=data2decode[14:16]      

    '''print("RPM: " + WDRPM)
    print("FAN: " + WDRPM)
    print("TEMP: " + WDTEMP)
    print("BACKLIGHT: " + WDBACKLIGHT)
    print("LED: " + WDLED)
    print("LED BLK: " + WDBLINK)
    print("LED PLS: " + WDLEDPULSE)
    print("UNASSIGNED: " + WDDRiVE)'''

def getButton(which):
    global WDALERT
    while True:
        print("getting button")
        checkForIncomingMail()
        time.sleep(1)
        print(WDALERT)
        if which == WDALERT:
            WDALERT=""
            print("breaking out")
            return True
        #else:
        #    return False

def getButtonidk():
    global WDALERT
    while True:
        print("getting button")
        checkForIncomingMail()
        time.sleep(1)
        print(WDALERT)
        if WDALERT != "":
            uh = WDALERT
            WDALERT=""
            if uh == btnU:
                return "UP"
            elif uh == btnD:
                return "DN"
            elif uh == btnH:
                return "HO"
            return

def getButtonHHold(which):
    global WDALERT
    while True:
        print("getting button hold")
        checkForIncomingMail()
        time.sleep(1)
        print(WDALERT)
        if which == WDALERT:
            WDALERT=""
            time.sleep(3)
            Send("STA")#62active 6a non act
            time.sleep(1)

            time.sleep(30)



            WDALERT=""
            print("breaking out")
            return True
        #else:
        #    return False
###########################################################################
#############################   Pages   ###################################
###########################################################################
def tutPage():
    Send(["FAN=32","LN1=UI Guide?    NO>","LN2=            YES>"])
   
    if getButton(btnD):
        Send(["LED=04","FAN=10","LN1=  Hello! I can","LN2=be slow to react"])
        time.sleep(5)
    
    Send(["LN1=  So please be","LN2=   patient :)"])
    time.sleep(8)
    Send(["LN1=    Lets Get","LN2=   Started!!!"])
    time.sleep(8)

    Send(["LN1=  -Navigation-","LN2="])
    time.sleep(8)
    Send(["LN1=Use Arrows To  >","LN2=Scroll Pages   >"])
    time.sleep(8)
    Send(["LN1=Try It! Goto","LN2=Next Page      >>"])

    if getButton(btnD):
        Send(["LN1=When on a screen","LN2=thats interactiv"])
        time.sleep(5)
        Send(["LED=14","LN1=the MENU button","LN2=will illuminate"])
        time.sleep(5)
        Send(["LED=14","LN1=   Learn More","LN2=    >ENTER<"])

    if getButton(btnH):
        Send(["LED=0C","PLS=00","LN1=Or it will show","LN2=red to EXIT"])
        time.sleep(5)
    
    Send(["LED=14","LN1=  -STATUS LED-","LN2=    >START<"])
    if getButton(btnH):
        Send(["LED=04","LN1=Scroll to Learn>","LN2=about each state"])

    sp=0
    cn=0
    while True:
        pushed = getButtonidk()
        if pushed == "UP":
            if sp > 8: 
                sp=1
            else:
                sp = sp + 1
            cn=True
        elif pushed == "DN":
            if sp == 0: 
                sp=8
            else:
                sp = sp - 1
            cn=True
        elif pushed == "HO" and sp == 8:
            Send(["LED=01"])
            break

        if cn==True:
            if sp == 1:
                Send(["LED=00","BLK=01","LN1=OS Booting","LN2=Please wait..."])
            elif sp == 2:
                Send(["LED=00","BLK=02","LN1=WDHW Backend","LN2=NOT RUNNING"])
            elif sp == 3:
                Send(["LED=00","BLK=06","LN1=Backend: Online","LN2=Software: Offline"])
            elif sp == 4:
                Send(["LED=06","BLK=00","LN1=Backend: Online","LN2=Software: Loading"])
            elif sp == 5:
                Send(["LED=01","PLS=00","LN1=All Systems","LN2=Opperational"])
            elif sp == 6:
                Send(["LED=00","PLS=01","LN1=Sleep Mode","LN2=Fully Opperational"])
            elif sp == 7:
                Send(["LED=01","PLS=00","BLK=02","LN1=System","LN2=Notification"])
            elif sp == 8:
                Send(["LED=00","BLK=00","PLS=00","LN1=     System","LN2=     >EXIT<"])

    print("tut done")

def welcomePage():
    Send(["LN1=   Welcome To", "LN2=  WD Hardware!", "LED=01"])

def mainPage():
    hostname=socket.gethostname()
    print(hostname)
    Send(["LED=01", "LN1=   TrueNAS @   ", ("LN2=" + hostname)])

def drivePage():
    Send(["LN1=OK   OK  OK   OK", "LN2=--F --F  --F --F"])

def ipPage():
    pass

def sysPage():
    pass


def settingsPage():
    pass

    


###########################################################################
#############################   MAIN   ####################################
###########################################################################
def execute_app():       # Main Execution Function
    global backendState
    global WDALERT
    count = 0
    print("Program Status: [ONLINE]")
    ProgramHealth="ONLINE"
    WDALERT=""

    # Start Loop - Checks for the backend being online before doing anything, timeouts after 60 seconds.
    while True:
        if count == 0:
            backendHealthCheck()
            print("Backend Server Status: [" + backendState + "]")
        if count > 60:
            print("Backend server failed to come online after 60 seconds... exiting...")
            backendState="OFFLINE"
            quit()
        count = count + 1 
        

        # The backend server daemon is ONLINE! LETS GET PUMPING!!
        if backendState == "ONLINE":
            print("Took [" + str(count) + "] Seconds To Do So.")
            count=0
            Handshake = welcomePage() # The Two programs take a few seconds to allign themselves, once this command goes through. We are set.

            # Main Loop
            tutPage()
            mainPage()
            while True:
                if backendState == "OFFLINE": break
                checkForIncomingMail()
                time.sleep(1)

def terminate_app():     # Function used when program terminates for any reason
    with open('daemonin.txt', 'w') as fileout: fileout.writelines( "OFFLINE\n\n\n" )
    fileout.close

def main():
    try:     # Run Man Application
        execute_app()
    finally: # If anthing happends to the Main Application, run this
        terminate_app()

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