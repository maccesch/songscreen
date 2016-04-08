from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QWidget, QToolButton, QStyle, QSlider, QHBoxLayout


class PlayerControlsWidget(QWidget):
    play = pyqtSignal()
    pause = pyqtSignal()
    # stop = pyqtSignal()
    # next = pyqtSignal()
    # previous = pyqtSignal()
    changeVolume = pyqtSignal(int)

    # changeMuting = pyqtSignal(bool)
    # changeRate = pyqtSignal(float)

    def __init__(self, parent=None):
        super(PlayerControlsWidget, self).__init__(parent)

        self.playerState = QMediaPlayer.StoppedState
        self.playerMuted = False

        self.playButton = QToolButton(clicked=self.playClicked)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.playButton.setStyleSheet("""
            QToolButton {
                background-color: #c3c3c3;
                border: none;
                border-radius: 3px;
                padding: 8px 16px 6px;
            }

            QToolButton:pressed {
                background-color: #c8c8c8;
            }
        """)

        # self.stopButton = QToolButton(clicked=self.stop)
        # self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        # self.stopButton.setEnabled(False)
        #
        # self.nextButton = QToolButton(clicked=self.next)
        # self.nextButton.setIcon(
        #     self.style().standardIcon(QStyle.SP_MediaSkipForward))
        #
        # self.previousButton = QToolButton(clicked=self.previous)
        # self.previousButton.setIcon(
        #     self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        #
        # self.muteButton = QToolButton(clicked=self.muteClicked)
        # self.muteButton.setIcon(
        #     self.style().standardIcon(QStyle.SP_MediaVolume))

        self.volumeSlider = QSlider(Qt.Horizontal,
                                    sliderMoved=self.changeVolume)
        self.volumeSlider.setRange(0, 100)

        # self.rateBox = QComboBox(activated=self.updateRate)
        # self.rateBox.addItem("0.5x", 0.5)
        # self.rateBox.addItem("1.0x", 1.0)
        # self.rateBox.addItem("2.0x", 2.0)
        # self.rateBox.setCurrentIndex(1)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.addWidget(self.stopButton)
        # layout.addWidget(self.previousButton)
        layout.addWidget(self.playButton)
        # layout.addWidget(self.nextButton)
        # layout.addWidget(self.muteButton)
        layout.addWidget(self.volumeSlider)
        # layout.addWidget(self.rateBox)
        self.setLayout(layout)

    def state(self):
        return self.playerState

    def setState(self, state):
        if state != self.playerState:
            self.playerState = state

            if state == QMediaPlayer.StoppedState:
                # self.stopButton.setEnabled(False)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))
            elif state == QMediaPlayer.PlayingState:
                # self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
            elif state == QMediaPlayer.PausedState:
                # self.stopButton.setEnabled(True)
                self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def volume(self):
        return self.volumeSlider.value()

    def setVolume(self, volume):
        self.volumeSlider.setValue(volume)

    # def isMuted(self):
    #     return self.playerMuted
    #
    # def setMuted(self, muted):
    #     if muted != self.playerMuted:
    #         self.playerMuted = muted
    #
    #         self.muteButton.setIcon(
    #             self.style().standardIcon(
    #                 QStyle.SP_MediaVolumeMuted if muted else QStyle.SP_MediaVolume))

    def playClicked(self):
        if self.playerState in (QMediaPlayer.StoppedState, QMediaPlayer.PausedState):
            self.play.emit()
        elif self.playerState == QMediaPlayer.PlayingState:
            self.pause.emit()

            # def muteClicked(self):
            #     self.changeMuting.emit(not self.playerMuted)
            #
            # def playbackRate(self):
            #     return self.rateBox.itemData(self.rateBox.currentIndex())
            #
            # def setPlaybackRate(self, rate):
            #     for i in range(self.rateBox.count()):
            #         if qFuzzyCompare(rate, self.rateBox.itemData(i)):
            #             self.rateBox.setCurrentIndex(i)
            #             return
            #
            #     self.rateBox.addItem("%dx" % rate, rate)
            #     self.rateBox.setCurrentIndex(self.rateBox.count() - 1)
            #
            # def updateRate(self):
            #     self.changeRate.emit(self.playbackRate())