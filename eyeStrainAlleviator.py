import os

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

def changeDisplayBrightness(strain):

    assert strain == 0 or strain == 1 or strain == 2

    currBrightness = getCurrentBrightness()

    newBrightness = currBrightness - 0.1 * strain
    brightnessCmd = "brightness {val}".format(val = newBrightness)

    os.system(brightnessCmd)
    return newBrightness
