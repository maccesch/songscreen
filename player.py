#!/usr/bin/env python

import json
import os

from PyQt5.QtCore import (pyqtSignal, QFileInfo, Qt,
                          QTime, QUrl)
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtMultimedia import (QMediaContent,
                                QMediaMetaData, QMediaPlayer, QMediaPlaylist)
from PyQt5.QtWidgets import (QApplication, QDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QSlider, QVBoxLayout, QWidget)

from media_progress_widget import MediaMarker, MediaProgressWidget
from player_controls_widget import PlayerControlsWidget
from screen_select_widget import ScreenSelectWidget
from song_select_widget import SongSelectWidget
from song_text_widget import SongTextWidget
from settings_widget import SettingsWidget


class Player(QWidget):
    audio_path = "audio"
    lyrics_path = os.path.join("lyrics", "de")
    timings_path = os.path.join("lyrics", "timing")
    settings_path = "settings.json"

    fullScreenChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(Player, self).__init__(parent)

        self.colorDialog = None
        self.trackInfo = ""
        self.statusInfo = ""
        self.duration = 0

        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        self.player.durationChanged.connect(self.durationChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.player.metaDataChanged.connect(self.metaDataChanged)
        # self.playlist.currentIndexChanged.connect(self.playlistPositionChanged)
        self.player.mediaStatusChanged.connect(self.statusChanged)
        self.player.bufferStatusChanged.connect(self.bufferingProgress)
        self.player.videoAvailableChanged.connect(self.videoAvailableChanged)
        self.player.error.connect(self.displayErrorMessage)

        # self.videoWidget = VideoWidget()
        # self.player.setVideoOutput(self.videoWidget)

        self.slider = MediaProgressWidget()  # QSlider(Qt.Horizontal)
        self.markers = []

        self.songtext_widget = SongTextWidget()
        self.songtext_widget.show()

        # self.playlistModel = PlaylistModel()
        # self.playlistModel.setPlaylist(self.playlist)
        #
        # self.playlistView = QListView()
        # self.playlistView.setModel(self.playlistModel)
        # self.playlistView.setCurrentIndex(
        #     self.playlistModel.index(self.playlist.currentIndex(), 0))
        #
        # self.playlistView.activated.connect(self.jump)

        self.slider.setRange(0, self.player.duration() / 1000)

        self.labelDuration = QLabel()
        self.slider.sliderMoved.connect(self.seek)

        # openButton = QPushButton("Open", clicked=self.open)

        controls = PlayerControlsWidget()
        controls.setState(self.player.state())
        controls.setVolume(self.player.volume())
        # controls.setMuted(controls.isMuted())

        controls.play.connect(self.player.play)
        controls.pause.connect(self.player.pause)
        # controls.stop.connect(self.player.stop)
        # controls.stop.connect(self.videoWidget.update)
        # controls.next.connect(self.playlist.next)
        # controls.previous.connect(self.previousClicked)
        controls.changeVolume.connect(self.player.setVolume)
        # controls.changeMuting.connect(self.player.setMuted)
        # controls.changeRate.connect(self.player.setPlaybackRate)

        self.player.stateChanged.connect(controls.setState)
        self.player.stateChanged.connect(self.setState)
        self.player.volumeChanged.connect(controls.setVolume)
        # self.player.mutedChanged.connect(controls.setMuted)

        # self.fullScreenButton = QPushButton("FullScreen")
        # self.fullScreenButton.setCheckable(True)
        #
        # self.colorButton = QPushButton("Color Options...")
        # self.colorButton.setEnabled(False)
        # self.colorButton.clicked.connect(self.showColorDialog)

        displayLayout = QHBoxLayout()
        # displayLayout.addWidget(self.videoWidget, 2)
        # displayLayout.addWidget(self.songtext_widget)
        # displayLayout.addWidget(self.playlistView)

        self.song_select_widget = SongSelectWidget(self.available_song_numbers)
        self.song_select_widget.song_selected.connect(self.load_song)

        self.screen_select_widget = ScreenSelectWidget()
        self.screen_select_widget.screen_selected.connect(self.display_lyrics_on_screen)
        self.screen_select_widget.active_screen = QApplication.desktop().screenNumber(self.songtext_widget)

        self.settings_button = QPushButton()
        self.settings_button.setText("Einstellungen...")
        self.settings_button.clicked.connect(self.show_settings)

        sidebarLayout = QVBoxLayout()
        # sidebarLayout.setContentsMargins(10, 11, 0, 2);

        sidebarLayout.addWidget(self.settings_button)
        sidebarLayout.addStretch(1);
        sidebarLayout.addWidget(self.screen_select_widget)

        displayLayout.addWidget(self.song_select_widget)
        displayLayout.addLayout(sidebarLayout)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        # controlLayout.addWidget(openButton)
        # controlLayout.addStretch(1)
        controlLayout.addWidget(controls)
        controlLayout.addStretch(1)
        controlLayout.addWidget(self.labelDuration)
        # controlLayout.addWidget(self.fullScreenButton)
        # controlLayout.addWidget(self.colorButton)

        layout = QVBoxLayout()
        layout.addLayout(displayLayout)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self.slider)
        # hLayout.addWidget(self.labelDuration)
        layout.addLayout(hLayout)
        layout.addLayout(controlLayout)

        self.setLayout(layout)

        if not self.player.isAvailable():
            QMessageBox.warning(self, "Service not available",
                                "The QMediaPlayer object does not have a valid service.\n"
                                "Please check the media service plugins are installed.")

            controls.setEnabled(False)
            self.playlistView.setEnabled(False)
            # openButton.setEnabled(False)
            self.colorButton.setEnabled(False)
            self.fullScreenButton.setEnabled(False)

        self.metaDataChanged()

        self._loading_audio = False
        self._finished_song = False
        self._lyrics_fading = False

        self._song_number = -1

        self.settings = {
            'font_size': 40,
        }
        self._load_settings()

        self.settings_widget = SettingsWidget(self.settings)
        self.settings_widget.font_size_changed.connect(self.songtext_widget.set_font_size)

    @property
    def available_song_numbers(self):
        audios = set(
            [int(os.path.splitext(filename)[0]) for filename in os.listdir(self.audio_path) if filename[0] != '.'])
        lyrics = set(
            [int(os.path.splitext(filename)[0]) for filename in os.listdir(self.lyrics_path) if filename[0] != '.'])

        return sorted(list(audios.intersection(lyrics)))

    def show_settings(self):
        self.settings_widget.hide()
        self.settings_widget.show()

    def display_lyrics_on_screen(self, screen_number):
        desktop = QApplication.desktop()

        if screen_number >= desktop.screenCount():
            screen_number = desktop.screenNumber(self)

        rect = desktop.availableGeometry(screen_number)

        if screen_number != desktop.screenNumber(self):
            self.songtext_widget.setWindowFlags(Qt.FramelessWindowHint)
            self.songtext_widget.show()
            self.songtext_widget.hide()
            self.songtext_widget.move(rect.x(), rect.y())
            self.songtext_widget.resize(rect.width(), rect.height())
            self.songtext_widget.showFullScreen()
        else:
            self.songtext_widget.setWindowFlags(Qt.WindowTitleHint)
            self.songtext_widget.show()
            self.songtext_widget.hide()
            self.songtext_widget.move(rect.x(), rect.y())
            self.songtext_widget.resize(self.songtext_widget.minimumSize())

            self.songtext_widget.show()

        self.screen_select_widget.active_screen = screen_number

        self.activateWindow()

    def load_song(self, song_number):
        if self._song_number == song_number:
            self.seek(0)
        else:
            if self._song_number > 0:
                self._save_timings()

            self._song_number = song_number
            self.slider.dirty = False
            self._load_audio(self._song_number)
            self._load_lyrics(self._song_number)

        # self.player.play()

    def _load_audio(self, song_number):
        filename = os.path.join(self.audio_path, "{:03}.m4a".format(song_number))
        self.playlist.clear()
        fileInfo = QFileInfo(filename)
        if fileInfo.exists():
            url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
            if fileInfo.suffix().lower() == 'm3u':
                self.playlist.load(url)
            else:
                self.playlist.addMedia(QMediaContent(url))
                self._loading_audio = True

            self.player.play()

    def _load_lyrics(self, song_number):
        with open(os.path.join(self.lyrics_path, "{}.json".format(song_number)), 'r') as f:
            song_markers = json.load(f)

            self.markers = []

            for m in song_markers['markers']:
                marker = MediaMarker(self.slider, m['name'])
                marker.text = m['text']
                marker.progress = 0.0
                self.markers.append(marker)

            self.songtext_widget.title = "{}  {}".format(song_number, song_markers['title'])
            self.songtext_widget.markers = self.markers
            self.songtext_widget.fade_in()

        try:
            with open(os.path.join(self.timings_path, "{}.json".format(song_number)), 'r') as f:
                timings = json.load(f)
                for m, t in zip(self.markers, timings):
                    m.progress = t
        except FileNotFoundError:
            pass

        self.slider.markers = self.markers

    # def open(self):
    #     fileNames, _ = QFileDialog.getOpenFileNames(self, "Open Files")
    #     self.addToPlaylist(fileNames)
    #
    # def addToPlaylist(self, fileNames):
    #     for name in fileNames:
    #         fileInfo = QFileInfo(name)
    #         if fileInfo.exists():
    #             url = QUrl.fromLocalFile(fileInfo.absoluteFilePath())
    #             if fileInfo.suffix().lower() == 'm3u':
    #                 self.playlist.load(url)
    #             else:
    #                 self.playlist.addMedia(QMediaContent(url))
    #         else:
    #             url = QUrl(name)
    #             if url.isValid():
    #                 self.playlist.addMedia(QMediaContent(url))

    def durationChanged(self, duration):
        duration /= 1000

        self.duration = duration
        self.slider.setMaximum(duration)

        if self._loading_audio:
            self._loading_audio = False

            line_total = 0
            for marker in self.markers:
                line_total += marker.linecount - 1

            silence_ratio = 5.0 / self.duration
            offset = 1.8 / line_total

            linecount = 0
            for marker in self.markers:
                if marker.progress == 0.0:
                    marker.progress = offset + (1 - offset) * (1 - silence_ratio) * linecount / line_total
                linecount += marker.linecount - 1

            # self.player.pause()

    @property
    def _should_fade_out(self):
        return self.player.position() / 1000 >= self.duration - 4

    def positionChanged(self, progress):
        progress /= 1000

        if not self.slider.isSliderDown():
            self.slider.setValue(progress)

        self.updateDurationInfo(progress)

        if self.duration > 0:
            # if self.player.state() == QMediaPlayer.PlayingState:
            self.songtext_widget.progress = progress / self.duration

            if self._should_fade_out:
                if not self._lyrics_fading:
                    self._lyrics_fading = True
                    self.songtext_widget.fade_out()

    def metaDataChanged(self):
        if self.player.isMetaDataAvailable():
            self.setTrackInfo("%s - %s" % (
                self.player.metaData(QMediaMetaData.AlbumArtist),
                self.player.metaData(QMediaMetaData.Title)))

    def previousClicked(self):
        # Go to the previous track if we are within the first 5 seconds of
        # playback.  Otherwise, seek to the beginning.
        if self.player.position() <= 5000:
            self.playlist.previous()
        else:
            self.player.setPosition(0)

    def jump(self, index):
        if index.isValid():
            self.playlist.setCurrentIndex(index.row())
            self.player.play()

    def playlistPositionChanged(self, position):
        self.playlistView.setCurrentIndex(
            self.playlistModel.index(position, 0))

    def seek(self, seconds):
        self.player.setPosition(seconds * 1000)

    def setState(self, status):

        if status == QMediaPlayer.StoppedState:
            self._finished_song = True

        elif status == QMediaPlayer.PlayingState:
            if self._finished_song or (self._lyrics_fading and not self._should_fade_out):
                self._finished_song = False
                self._lyrics_fading = False
                self.songtext_widget.fade_in()

    def statusChanged(self, status):
        self.handleCursor(status)

        if status == QMediaPlayer.LoadingMedia:
            self.setStatusInfo("Loading...")
        elif status == QMediaPlayer.StalledMedia:
            self.setStatusInfo("Media Stalled")
        elif status == QMediaPlayer.EndOfMedia:
            QApplication.alert(self)
        elif status == QMediaPlayer.InvalidMedia:
            self.displayErrorMessage()
        else:
            self.setStatusInfo("")

    def handleCursor(self, status):
        if status in (QMediaPlayer.LoadingMedia, QMediaPlayer.BufferingMedia, QMediaPlayer.StalledMedia):
            self.setCursor(Qt.BusyCursor)
        else:
            self.unsetCursor()

    def bufferingProgress(self, progress):
        self.setStatusInfo("Buffering %d%" % progress)

    def videoAvailableChanged(self, available):
        if available:
            self.fullScreenButton.clicked.connect(
                self.videoWidget.setFullScreen)
            self.videoWidget.fullScreenChanged.connect(
                self.fullScreenButton.setChecked)

            if self.fullScreenButton.isChecked():
                self.videoWidget.setFullScreen(True)
        else:
            self.fullScreenButton.clicked.disconnect(
                self.videoWidget.setFullScreen)
            self.videoWidget.fullScreenChanged.disconnect(
                self.fullScreenButton.setChecked)

            self.videoWidget.setFullScreen(False)

        self.colorButton.setEnabled(available)

    def setTrackInfo(self, info):
        self.trackInfo = info

        if self.statusInfo != "":
            self.setWindowTitle("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.setWindowTitle(self.trackInfo)

    def setStatusInfo(self, info):
        self.statusInfo = info

        if self.statusInfo != "":
            self.setWindowTitle("%s | %s" % (self.trackInfo, self.statusInfo))
        else:
            self.setWindowTitle(self.trackInfo)

    def displayErrorMessage(self):
        self.setStatusInfo(self.player.errorString())

    def updateDurationInfo(self, currentInfo):
        duration = self.duration
        if currentInfo or duration:
            currentTime = QTime((currentInfo / 3600) % 60, (currentInfo / 60) % 60,
                                currentInfo % 60, (currentInfo * 1000) % 1000)
            totalTime = QTime((duration / 3600) % 60, (duration / 60) % 60,
                              duration % 60, (duration * 1000) % 1000);

            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)

    def showColorDialog(self):
        if self.colorDialog is None:
            brightnessSlider = QSlider(Qt.Horizontal)
            brightnessSlider.setRange(-100, 100)
            brightnessSlider.setValue(self.videoWidget.brightness())
            brightnessSlider.sliderMoved.connect(
                self.videoWidget.setBrightness)
            self.videoWidget.brightnessChanged.connect(
                brightnessSlider.setValue)

            contrastSlider = QSlider(Qt.Horizontal)
            contrastSlider.setRange(-100, 100)
            contrastSlider.setValue(self.videoWidget.contrast())
            contrastSlider.sliderMoved.connect(self.videoWidget.setContrast)
            self.videoWidget.contrastChanged.connect(contrastSlider.setValue)

            hueSlider = QSlider(Qt.Horizontal)
            hueSlider.setRange(-100, 100)
            hueSlider.setValue(self.videoWidget.hue())
            hueSlider.sliderMoved.connect(self.videoWidget.setHue)
            self.videoWidget.hueChanged.connect(hueSlider.setValue)

            saturationSlider = QSlider(Qt.Horizontal)
            saturationSlider.setRange(-100, 100)
            saturationSlider.setValue(self.videoWidget.saturation())
            saturationSlider.sliderMoved.connect(
                self.videoWidget.setSaturation)
            self.videoWidget.saturationChanged.connect(
                saturationSlider.setValue)

            layout = QFormLayout()
            layout.addRow("Brightness", brightnessSlider)
            layout.addRow("Contrast", contrastSlider)
            layout.addRow("Hue", hueSlider)
            layout.addRow("Saturation", saturationSlider)

            button = QPushButton("Close")
            layout.addRow(button)

            self.colorDialog = QDialog(self)
            self.colorDialog.setWindowTitle("Color Options")
            self.colorDialog.setLayout(layout)

            button.clicked.connect(self.colorDialog.close)

        self.colorDialog.show()

    def closeEvent(self, close_event):
        self._save_timings()
        self._save_settings()
        self.songtext_widget.close()
        self.settings_widget.close()

    def _save_timings(self):
        if self.slider.dirty:
            with open(os.path.join(self.timings_path, "{}.json".format(self._song_number)), 'w') as f:
                json.dump([marker.progress for marker in self.markers], f, indent=2)

    def _save_settings(self):
        with open(self.settings_path, 'w') as f:
            self.settings.update({
                'lyrics_screen': QApplication.desktop().screenNumber(self.songtext_widget),
                'control_window_position': [self.x(), self.y()],
            })

            json.dump(self.settings, f, indent=2)

    def _load_settings(self):
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)

                if 'lyrics_screen' in settings.keys():
                    self.display_lyrics_on_screen(settings['lyrics_screen'])

                if 'control_window_position' in settings.keys():
                    self.move(*settings['control_window_position'])

                self.settings.update(settings)

                self.songtext_widget.set_font_size(self.settings['font_size'])

        except FileNotFoundError:
            pass


if __name__ == '__main__':
    import sys

    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        frozen = 'ever so'
        bundle_dir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    os.chdir(bundle_dir)

    app = QApplication(sys.argv)

    QFontDatabase.addApplicationFont("font/FiraSans-Regular.otf")
    QFontDatabase.addApplicationFont("font/FiraSans-Medium.otf")
    QFontDatabase.addApplicationFont("font/FiraSans-SemiBold.otf")

    player = Player()
    player.show()

    sys.exit(app.exec_())
