import sys
import time

import cv2

import PyQt5
import os
import numpy as np
import image_recognition as recognition
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi


directory = os.path.join(os.path.dirname(__file__), '..')
output_image = os.path.join(directory, 'recognition', 'output_photos', 'output.jpg')
retrained_labels = os.path.join(directory, 'recognition', 'retrained_labels.txt')


class CaptureThread(QThread):
    update_pixmap = pyqtSignal(QImage)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                self.update(frame)

    def update(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # define range of blue color in HSV
        lower_blue = np.array([110, 50, 50])
        upper_blue = np.array([130, 255, 255])

        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        cv2.bitwise_and(frame, frame, mask=mask)

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        q_conversion = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888)
        pixmap = q_conversion.scaled(480, 480, PyQt5.QtCore.Qt.KeepAspectRatio)
        self.update_pixmap.emit(pixmap)


class CountDownThread(QThread):
    update_timer = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.timer = 4

    def run(self):
        if self.timer == 0:
            return

        self.timer -= 1
        self.update_timer.emit(self.timer)
        time.sleep(1)
        self.run()


class RPSGame(QMainWindow):

    def __init__(self):
        super(RPSGame, self).__init__()
        loadUi('window.ui', self)
        self.timer_thread = None
        self.latest_image = None
        self.thread = CaptureThread(self)
        self.playButton.clicked.connect(self.start_game)

        self.start_capture()

    def start_capture(self):
        self.thread.update_pixmap.connect(self.display_image)
        self.thread.start()

    def start_game(self):
        self.timer_thread = CountDownThread()
        self.timer_thread.update_timer.connect(self.countdown)
        self.timer_thread.start()

    @pyqtSlot(QImage)
    def display_image(self, image):
        self.latest_image = image
        self.videoDisplay.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(int)
    def countdown(self, time):
        self.timeLabel.setText(str(time))
        if time == 0:
            self.write_picture()
            value = recognition.identify_image(output_image)

    def write_picture(self):
        self.latest_image.save(output_image)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RPSGame()
    window.setWindowTitle('Rock Paper Scissors')
    window.show()
    sys.exit(app.exec_())
