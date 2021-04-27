import glob
from serial import Serial
import signal
import re
import numpy as np
from PIL import Image
import time

class TimeoutException(Exception):   # Custom exception class
    pass

def break_after(seconds=1):
    def timeout_handler(signum, frame):   # Custom signal handler
        raise TimeoutException
    def function(function):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                res = function(*args, **kwargs)
                signal.alarm(0)      # Clear alarm
                return res
            except TimeoutException:
                print('Oops, timeout: {seconds} sec reached.'.format(seconds = seconds), function.__name__, args, kwargs)
            return
        return wrapper
    return function

def getPorts():
    return glob.glob('/dev/tty.*')

def serialReadAmbient(port):
        s = Serial(port=port, baudrate=9600)
        val = s.readline()
        if val:
            return val

@break_after(5)
def serialReadAmbientAll():
    val = serialReadAmbient(getPorts()[-1])
    if val:
        val = str(val)
        found = re.search(".*[0-9]*.*", val)
        if found:
            matches = re.findall("[0-9]*", val)
            for match in matches:
                if match:
                    return match
    return "Error"

#Modify to get row by row instead of whole thing at once
@break_after(20)
def serialReadImage():
        s = Serial(port=getPorts()[-1], baudrate=1000000)
        while True:
            val = str(s.readline())
            if val.find("image") != 0:
                break
        val = s.read(320*240)
        if val:
            intVals = [x for x in val]
            print(intVals)
            arr = np.array(intVals).reshape(240, 320)
            arr = arr.astype(np.uint8)
            im = Image.fromarray(arr)
            im.save("imageRead.png")
            return


if __name__ == "__main__":
    # print(getPorts())
    # while True:
    #     print(serialReadAmbientAll())
    start = time.time()
    frames = 0
    while True:
        serialReadImage()
        frames += 1
    print("Frames/Sec:", frames / time.time() - start)
