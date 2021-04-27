from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap, QImage
import sys
import time
import threading
import cv2
import queue as Queue

from MainWindow import Ui_MainWindow
import blinkDetection
import eyeStrainAlleviator
import serialRead

continuous = False

IMG_SIZE    = 1280,720          # 640,480 or 1280,720 or 1920,1080
IMG_FORMAT  = QImage.Format_RGB888
DISP_SCALE  = 3               # Scaling factor for display image
DISP_MSEC   = 50                # Delay between display cycles
CAP_API     = cv2.CAP_ANY       # API: CAP_ANY or CAP_DSHOW etc...
EXPOSURE    = 0                 # Zero for automatic exposure

camera_num  = 1                 # Default camera (first in list)
image_queue = Queue.Queue()     # Queue to hold images
capturing   = True              # Flag to indicate capturing
runningEventLoop = False

imgRun = cv2.imread("running.jpeg")

# Grab images from the camera (separate thread)
def grab_images(cam_num, queue):
    cap = cv2.VideoCapture(cam_num-1 + CAP_API)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMG_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_SIZE[1])
    if EXPOSURE:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
        cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE)
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    while capturing:
        if runningEventLoop:
            queue.put(imgRun)
            time.sleep(1)
        elif cap.grab():
            retval, image = cap.retrieve(0)
            if image is not None and queue.qsize() < 2:
                queue.put(image)
            else:
                time.sleep(DISP_MSEC / 1000.0)
    cap.release()

# Step 1: Create a worker class
class Worker(QObject):
    finished = pyqtSignal()
    label = pyqtSignal(str)
    progress = pyqtSignal(int)

    infoLabels = pyqtSignal(str, str, str, str)

    def loop(self):
        while True:
            self.label.emit("Recording Video...")
            self.run()
            self.label.emit("Done. Wait 30 seconds till next iteration.")
            time.sleep(30)

    def run(self):
        """Long-running task."""
        start = time.time()
        blinkDetection.clear_saved_data()
        status = blinkDetection.save_video()
        if status == "Error":
            self.label.emit("Could not detect camera")
            self.progress.emit(0)
            if not continuous:
                self.finished.emit()
            return
        else:
            self.progress.emit(30)
        self.label.emit("Analyzing Video To Detect Blinks")
        bPM = blinkDetection.run_live_blink_detector()
        if bPM == 0:
            self.label.emit("Could not detect blinks. Please make sure your face is visible under good lighting conditions.")
            self.progress.emit(0)
            time.sleep(5)
            if not continuous:
                self.finished.emit()
            return
        self.progress.emit(90)
        self.label.emit("Changing Display Brightness Accordingly")
        strain = eyeStrainAlleviator.convertBlinkRateToStrain(bPM)
        strainLevel = eyeStrainAlleviator.strainsReverse[strain]
        brightness = eyeStrainAlleviator.getCurrentBrightness()
        if strain != 0:
            brightness = eyeStrainAlleviator.changeDisplayBrightness(strain)
            self.label.emit("Display Brightness adjusted")
        else:
            self.label.emit("No strain detected")
        end = time.time()
        totalTime = end - start
        self.infoLabels.emit(str(bPM), strainLevel, str(brightness), str(totalTime))
        self.progress.emit(100)
        if not continuous:
            self.finished.emit()
        return

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.beginButton.pressed.connect(self.begin)
        self.calibrateButton.pressed.connect(self.calibrate)

        self.ambientLight.setText("N/A")
        self.blinksPerMinute.setText("N/A")
        self.eyeStrain.setText("N/A")
        self.brightness.setText(str(eyeStrainAlleviator.getCurrentBrightness()))
        self.progressBar.setValue(0)

    def calibrate(self):
        ambLight = eyeStrainAlleviator.changeBrightnessFromAmbient()
        if ambLight != "Error":
            self.ambientLight.setText(str(ambLight) + " lux")
        else:
            self.ambientLight.setText("Error")

    def eventLoop(self):
        global runningEventLoop
        runningEventLoop = False
        self.calibrateButton.setEnabled(True)
        self.beginButton.setEnabled(True)

    def begin(self):

        global runningEventLoop
        runningEventLoop = True

        self.consoleOutput.setText("Recording Video...")

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        if continuous == False:
            self.thread.started.connect(self.worker.run)
        else:
            self.thread.started.connect(self.worker.loop)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.label.connect(self.updateLabel)
        self.worker.progress.connect(self.reportProgress)
        self.worker.infoLabels.connect(self.updateInfoLabels)
        # Step 6: Start the thread
        self.thread.start()

        # Final resets
        self.beginButton.setEnabled(False)
        self.calibrateButton.setEnabled(False)
        self.thread.finished.connect(self.eventLoop)

    def updateLabel(self, text):
        self.consoleOutput.setText(text)

    def reportProgress(self, progress):
        self.progressBar.setValue(progress)

    def updateInfoLabels(self, bPM, strainLevel, brightness, totalTime):
        self.blinksPerMinute.setText(bPM)
        self.eyeStrain.setText(strainLevel)
        self.brightness.setText(brightness)
        self.consoleOutput.setText("Total time taken: " + totalTime + " (secs)")

    # Start image capture & display
    def start(self):

        capturing = True
        self.timer = QTimer(self)           # Timer to trigger display
        self.timer.timeout.connect(lambda:
                    self.show_image(image_queue, self.webcamFeed, DISP_SCALE))
        self.timer.start(DISP_MSEC)
        self.capture_thread = threading.Thread(target=grab_images,
                    args=(camera_num, image_queue))
        self.capture_thread.start()         # Thread to grab images

    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.display_image(img, display, scale)

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=1):
        disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_bpl = disp_size[0] * 3
        if scale > 1:
            img = cv2.resize(img, disp_size,
                             interpolation=cv2.INTER_CUBIC)
        qimg = QImage(img.data, disp_size[0], disp_size[1],
                      disp_bpl, IMG_FORMAT)
        qimgPix = QPixmap(qimg)
        display.setPixmap(qimgPix)

    # Window is closing: stop video capture
    def closeEvent(self, event = None):
        global capturing
        capturing = False
        self.capture_thread.join()

def main():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.start()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
