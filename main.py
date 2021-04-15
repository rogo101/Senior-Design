from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
import sys
import time

from MainWindow import Ui_MainWindow
import blinkDetection
import eyeStrainAlleviator

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.beginButton.pressed.connect(self.begin)

        self.ambientLight.setText("N/A")
        self.blinksPerMinute.setText("N/A")
        self.eyeStrain.setText("N/A")
        self.brightness.setText(str(eyeStrainAlleviator.getCurrentBrightness()))
        self.progressBar.setValue(20)

    def begin(self):
        self.consoleOutput.setText("Recording Video...")
        blinkDetection.clear_saved_data()
        status = blinkDetection.save_video()
        if status == "Error":
            self.consoleOutput.setText("Please connect a valid camera.")
            return
        else:
            self.progressBar.setValue(20)
        self.consoleOutput.setText("Analyzing Video To Detect Blinks")
        bPM = blinkDetection.run_live_blink_detector()
        self.blinksPerMinute.setText(str(bPM))
        self.progressBar.setValue(95)
        self.consoleOutput.setText("Changing Display Brightness Accordingly")
        strain = eyeStrainAlleviator.convertBlinkRateToStrain(bPM)
        strainLevel = eyeStrainAlleviator.strainsReverse[strain]
        self.eyeStrain.setText(strainLevel)
        if strain != 0:
            brightness = eyeStrainAlleviator.changeDisplayBrightness(strain)
            self.brightness.setText(str(brightness))
            self.consoleOutput.setText("Display Brightness adjusted")
        else:
            self.consoleOutput.setText("No strain detected")
        self.progressBar.setValue(100)
        return

def main():
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()
