import os
import time
import serialRead as sR
import numpy as np

strains = {"none": 0, "low": 1, "medium": 1.5, "high": 2}
strainsReverse = {0: "none", 1: "low", 1.5: "medium", 2:"high"}

def convertBlinkRateToStrain(blinksPerMinute):

    if blinksPerMinute < 8:
        return strains["high"]
    elif blinksPerMinute < 10:
        return strains["medium"]
    elif blinksPerMinute < 12:
        return strains["low"]
    else:
        return strains["none"]

def getCurrentBrightness():
    brightnessStream = os.popen("brightness -l")
    output = brightnessStream.read()
    outputList = output.split(" ")
    currBrightness = float(outputList[-1])
    return currBrightness

def changeDisplayBrightness(amount):

    currBrightness = getCurrentBrightness()

    newBrightness = currBrightness - 0.1 * amount
    if (newBrightness >= 0.99):
        newBrightness = 1.0
    brightnessCmd = "brightness {val}".format(val = newBrightness)

    os.system(brightnessCmd)
    return newBrightness

def changeBrightnessFromAmbient():
    ambs = []
    for i in range(0,3):
        val = sR.serialReadAmbientAll()
        if not val:
            return "Error"
        elif val == "Error":
            return "Error"
        else:
            val = int(val)
        ambs.append(val)
    amb = np.median(ambs)
    currBrightness = getCurrentBrightness()

    print("Ambient Lights:", ambs, "; Select:", amb)
    print("Current Brightness:", currBrightness)

    if amb < 30:
        newBrightness = amb/30 * currBrightness
        newBrightness = max(0.1, newBrightness) # minimum brightness
        while(getCurrentBrightness() > newBrightness + 0.1):
            changeDisplayBrightness(1)
            time.sleep(0.3)
    else:
        while(getCurrentBrightness() < 0.9):
            changeDisplayBrightness(-1)
            time.sleep(0.3)
        while(getCurrentBrightness() < 0.99):
            changeDisplayBrightness(-0.1)

    return amb

if __name__ == "__main__":
    while True:
        changeBrightnessFromAmbient()
