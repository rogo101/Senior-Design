import os

strains = {"none": 0, "low": 1, "medium": 2, "high": 3}
strainsReverse = {0: "none", 1 : "low", 2:"medium", 3:"high"}

def convertBlinkRateToStrain(blinksPerMinute):

    if blinksPerMinute < 12:
        return strains["low"]
    elif blinksPerMinute < 10:
        return strains["medium"]
    elif blinksPerMinute < 8:
        return strains["high"]
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
