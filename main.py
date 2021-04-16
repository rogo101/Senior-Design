from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
import sys
import time

from MainWindow import Ui_MainWindow
import blinkDetection
import eyeStrainAlleviator

# Step 1: Create a worker class
class Worker(QObject):
    finished = pyqtSignal()
    label = pyqtSignal(str)
    progress = pyqtSignal(int)

    infoLabels = pyqtSignal(str, str, str, str)

    def run(self):
        """Long-running task."""
        start = time.time()
        blinkDetection.clear_saved_data()
        status = blinkDetection.save_video()
        if status == "Error":
            self.label.emit("Could not detect camera")
            self.progress.emit(0)
            self.finished.emit()
            return
        else:
            self.progress.emit(30)
        self.label.emit("Analyzing Video To Detect Blinks")
        bPM = blinkDetection.run_live_blink_detector()
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
        self.finished.emit()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.beginButton.pressed.connect(self.begin)

        self.ambientLight.setText("N/A")
        self.blinksPerMinute.setText("N/A")
        self.eyeStrain.setText("N/A")
        self.brightness.setText(str(eyeStrainAlleviator.getCurrentBrightness()))
        self.progressBar.setValue(0)

    def begin(self):

        self.consoleOutput.setText("Recording Video...")

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
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
        self.thread.finished.connect(
            lambda: self.beginButton.setEnabled(True)
        )

    def updateLabel(self, text):
        self.consoleOutput.setText(text)

    def reportProgress(self, progress):
        self.progressBar.setValue(progress)

    def updateInfoLabels(self, bPM, strainLevel, brightness, totalTime):
        self.blinksPerMinute.setText(bPM)
        self.eyeStrain.setText(strainLevel)
        self.brightness.setText(brightness)
        time.sleep(5)
        self.consoleOutput.setText("Total time taken" + totalTime + " (secs)")



def main():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
