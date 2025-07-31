DO NOT USE, never finished, broked, and dead



# --InDev-- 

![Drag Racing](https://m.media-amazon.com/images/I/8127BVaefIL.jpg)

Version 1.1 (03-26-2024)
========================
* Added Support for Linux based TrueNAS Scale along side TrueNAS Core for PR4100 as per the request and help of @SuperDope & @nestandi
* Fixed Some Typos/Cleaned up while here
* More Comments = More Better

# WD PR4100 FreeNAS Hardware Control
 Hardware control for the WD PR4100 running [@stefaang's](https://github.com/stefaang) Freenas found [HERE](https://community.wd.com/t/firmware-freenas-on-pr4100-updated/218730). All work is based off his basic hardware control script found [here](https://gist.github.com/stefaang/0a23a25460f65086cbec0db526e87b03). I've simply made it better/more functional 

 ## Instalation:
 1. SSH into your FreeNas Box
 2. Make a directory in your prefered location to store managment scripts & enter it.
 3. Enter `git clone https://github.com/Coltonton/WD-PR4100-FreeNAS-Control` (or your repo)
 4. Enter `cd WD-PR4100-FreeNAS-Control`
 5. Enter `chmod +x wdpreinit.sh && chmod +x wdpostinit.sh && chmod +x wdshutdown.sh` 
 6. Close SSH and Enter your box's web UI
 7. Goto Tasks -> Init/Shutdown Scripts
 8. Click th + to add a new Task
 9. For `Type`, choose `Script` and choose the script you wish to add in the browser or by entering it's path
 10. For `When` select when you want each script to run (Pre-Init, Post-Init, Shutdown)
 1. Make sure enabled is checked
 12. Click `save`, reboot your box, and then enjoy! 

 Feel free to modify any of the scripts at your will and risk, a few things can be easily modified like PowerLED color, state, and Welcome Text. (Info on later, I do have some in the comments) 

## Added Features:
- TrueNAS Scale Support 
- Easy LED Control
- An actual Fan control profile (may need tuning use at your own risk)
- Seperate Scripts for Pre-Init / Post-Init(main) / Shutdown

## To Add:
- Maybe a full on device menu?
- Make easier for users to edit custom stuff / give options?

