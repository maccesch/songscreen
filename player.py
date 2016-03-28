#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited.
## Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################
import json
import os
import re
from functools import partial
from operator import attrgetter

from PyQt5.QtCore import (pyqtSignal, QAbstractItemModel,
                          QFileInfo, qFuzzyCompare, QModelIndex, QObject, Qt,
                          QTime, QUrl, QSize, QRectF, QPropertyAnimation, QEasingCurve, QAbstractAnimation)
from PyQt5.QtGui import QColor, QPainter, QPalette, QPen, QBrush, QFont, QFontMetricsF, QTransform, QFontDatabase
from PyQt5.QtMultimedia import (QMediaContent,
                                QMediaMetaData, QMediaPlayer, QMediaPlaylist)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QListView, QMessageBox,
                             QPushButton, QSizePolicy, QSlider, QStyle, QToolButton, QVBoxLayout, QWidget,
                             QAbstractSlider, QGraphicsScene, QGraphicsView, QGridLayout, QGraphicsObject,
                             QGraphicsOpacityEffect)


class ScreenSelectWidget(QWidget):
    screen_selected = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(ScreenSelectWidget, self).__init__(*args, **kwargs)

        self._active_screen = -1

        self._buttons = []


        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(QLabel("Textbildschirm"))
        self.setLayout(layout)

        self.refresh_widget()

        desktop = QApplication.desktop()
        desktop.screenCountChanged.connect(self.refresh_widget)
        # TODO : update to qt 5.6 and uncomment the next line
        # QApplication.instance().primaryScreenChanged.connect(self.refresh_widget)

    def refresh_widget(self, screen_count=0):

        layout = self.layout()
        for b in self._buttons:
            b.setParent(None)
            b.deleteLater()

        desktop = QApplication.desktop()

        self._buttons = []
        for i in range(screen_count if screen_count > 0 else desktop.screenCount()):
            button = QPushButton()
            button.setCheckable(True)
            button.setAutoExclusive(True)
            if i == self._active_screen:
                button.setChecked(True)
            button.setText("Bildschirm {}{}".format(
                i + 1,
                "" if desktop.screenNumber(self) != i else " (dieser)"
            ))
            layout.addWidget(button)
            button.pressed.connect(partial(self._screen_button_pressed, i))

            self._buttons.append(button)

        self.repaint()

    def _screen_button_pressed(self, screen_number):
        self.screen_selected.emit(screen_number)

    @property
    def active_screen(self):
        return self._active_screen

    @active_screen.setter
    def active_screen(self, value):
        layout = self.layout()

        if value >= len(self._buttons):
            value = len(self._buttons) - 1

        self._active_screen = value

        self._buttons[self._active_screen].setChecked(True)


class SongSelectWidget(QWidget):
    song_selected = pyqtSignal(int)

    def __init__(self, song_numbers, *args, **kwargs):
        super(SongSelectWidget, self).__init__(*args, **kwargs)


        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 8px 16px;
                margin: 2px;
            }

            QPushButton:pressed {
                background-color: #f9f9f9;
            }

            QPushButton:checked {
                background-color: #D5FCCD;
            }

            QPushButton:disabled {
                background-color: #f3f3f3;
            }
        """)

        layout = QGridLayout()
        layout.setHorizontalSpacing(1)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)

        # self.buttons = []
        for i in range(max(30, (song_numbers[-1] // 10 + 1) * 10)):
            button = QPushButton()
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setText(str(i + 1))
            button.setEnabled(i + 1 in song_numbers)

            layout.addWidget(button, i // 10, i % 10)
            button.pressed.connect(partial(self.song_button_pressed, i + 1))

    def song_button_pressed(self, song_number):
        self.song_selected.emit(song_number)


class MarkerMixin(object):
    def __init__(self, *args, **kwargs):
        super(MarkerMixin, self).__init__(*args, **kwargs)

        self._markers = []

    @property
    def markers(self):
        return self._markers

    @markers.setter
    def markers(self, value):
        for marker in self._markers:
            marker.changed.disconnect(self._markers_changed)

        self._markers = value

        for marker in self._markers:
            marker.changed.connect(self._markers_changed)

    def _markers_changed(self):
        raise NotImplementedError("You have to impement this in your subclass")


class SongTextCover(QGraphicsObject):
    def __init__(self, w, h, *args, **kwargs):
        super(SongTextCover, self).__init__(*args, **kwargs)

        self.w = w
        self.h = h

    def paint(self, qp, *args, **kwargs):
        qp.setPen(QPen(Qt.NoPen))
        qp.setBrush(QBrush(QColor(0, 0, 0)))
        qp.drawRect(self.boundingRect())

    def boundingRect(self):
        return QRectF(-100, -100, self.w + 200, self.h * 2)


class SongTextWidget(MarkerMixin, QGraphicsView):
    lines_per_screen = 8
    line_height_factor = 1.5
    scroll_lines = 2

    def __init__(self, *args, **kwargs):
        super(SongTextWidget, self).__init__(*args, **kwargs)

        self.w = 1920
        self.h = 1080

        self._progress = 0.0
        # self._animated_progress = 0.0

        self.title = ""

        self._linecount = 0

        self.setMinimumHeight(9 * 50)
        self.setMinimumWidth(16 * 50)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.HighQualityAntialiasing | QPainter.SmoothPixmapTransform)
        self.setInteractive(False)
        self.scene().setBackgroundBrush(Qt.black)

        self._line_height = 10
        self._document_height = 10

        self._animation = None

    def heightForWidth(self, width):
        return int(round(width / 16 * 9))

    def hasHeightForWidth(self):
        return True

    @property
    def _scroll_progress(self):
        if not self.markers:
            return self.progress

        if self.progress <= self.markers[0].progress:
            return 0.0

        past_line_count = 0
        current_marker = None
        next_marker_progress = 1
        for i, marker in enumerate(self.markers[:-1]):
            next_marker = self.markers[i + 1]
            if next_marker.progress > self.progress:
                current_marker = marker
                next_marker_progress = next_marker.progress
                break
            else:
                past_line_count += marker.linecount

        if next_marker_progress == 1:
            current_marker = self.markers[-1]

        return past_line_count / self._linecount + \
               (current_marker.linecount / self._linecount) * \
               (self.progress - current_marker.progress) / (next_marker_progress - current_marker.progress)

    @MarkerMixin.markers.setter
    def markers(self, value):
        MarkerMixin.markers.fset(self, value)

        self._linecount = 0
        for marker in self._markers:
            self._linecount += marker.linecount

        self._build_scene()

    def _markers_changed(self):
        self.repaint()

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self._update_screen_rect()

    def _update_screen_rect(self):
        if self._animation is not None and self._animation.state() == QAbstractAnimation.Running:
            return

        vertical_offset_bias = self.h * 0
        vertical_offset = self._scroll_progress * self._document_height

        if vertical_offset <= vertical_offset_bias:
            vertical_offset = 0
        else:
            vertical_offset = min(vertical_offset - vertical_offset_bias,
                                  (self._linecount - self.lines_per_screen * 0.6) * self._line_height)

        diff = self.sceneRect().y() - vertical_offset
        if abs(diff) > self._line_height * self.scroll_lines:
            factor = -int(diff) // int(self._line_height * self.scroll_lines)
            self._animation = QPropertyAnimation(self, b"sceneRect")
            self._animation.setDuration(2000)
            self._animation.setStartValue(self.sceneRect())
            y = self.sceneRect().y() + (self._line_height * self.scroll_lines) * factor
            y = max(0, y)
            self._animation.setEndValue(
                QRectF(0, y, self.w, self.h))
            self._animation.setEasingCurve(QEasingCurve.InOutQuad)
            self._animation.start()
            # self.setSceneRect(QRectF(0, self.sceneRect().y() + self._line_height * self.scroll_lines, w, h))

    def _build_scene(self):
        scene = self.scene()
        scene.setBackgroundBrush(Qt.white)
        scene.clear()

        font_size = self._calc_font_size(self.h)

        title_font = QFont('Fira Sans', font_size, QFont.Medium)
        default_font = QFont('Fira Sans', font_size, QFont.Normal)
        default_font.setHintingPreference(QFont.PreferFullHinting)
        default_font.setLetterSpacing(QFont.PercentageSpacing, 99)
        heading_font = QFont('Fira Sans', font_size * 0.7, QFont.DemiBold)

        default_color = QColor(0, 0, 0)
        heading_color = QColor(180, 180, 180)

        self._line_height = self._calc_line_height(default_font)
        self._document_height = self._calc_document_height(self._line_height)

        # scene.addRect(0.0, 0.0, self.w, self._document_height * 1.2, QPen(Qt.NoPen), QBrush(Qt.NoBrush))

        title = scene.addText(self.title, title_font)
        left = self.w / 50
        title.setPos(left, self._line_height)
        title.setDefaultTextColor(default_color)

        def add_line(text, offset=0, font=default_font, color=default_color):
            y = self._line_height * line_index + offset + self.h * 0.2

            metrics = QFontMetricsF(font)
            text_width = metrics.width(text)
            max_text_width = (self.w - left - left)
            overflow = text_width - max_text_width

            text = scene.addText(text, font)
            text.setPos(left, y)
            text.setDefaultTextColor(color)

            if overflow > 0:
                text.setTransform(QTransform().scale(1.0 - overflow / max_text_width, 1.0))

        line_index = 1
        for marker in sorted(self.markers, key=attrgetter("progress")):

            add_line(marker.name, offset=self._line_height * 0.2, font=heading_font, color=heading_color)
            line_index += 1

            for line in marker.text.splitlines():
                add_line(line)
                line_index += 1

        # self._document_cover = scene.addRect(-self.w * 0.5, -self._document_height * 0.5, self.w * 2, self._document_height * 2,
        #                                      QPen(Qt.NoPen), QBrush(QColor(0, 0, 0)))
        # self._document_cover.setOpacity(1)
        # self._document_cover_animation = OpacityAnimation(self._document_cover)
        # self._document_cover_animation = QPropertyAnimation(self._document_cover, b"opacity", self)
        # self._document_cover_animation.setDuration(1000)
        # self._document_cover_animation.setStartValue(1)
        # self._document_cover_animation.setStartValue(0)
        # self._document_cover_animation.start()


        self._document_cover = SongTextCover(self.w, self._document_height)
        scene.addItem(self._document_cover)
        self._document_cover.opacityChanged.connect(self._redraw_scene)

        self.setSceneRect(QRectF(0, 0, self.w, self.h))

        self.fitInView(QRectF(0, 0, self.w, self.h), Qt.KeepAspectRatio)

    def fade_in(self):
        self._document_cover_animation = QPropertyAnimation(self._document_cover, b"opacity")

        self._document_cover_animation.setDuration(1000)
        self._document_cover_animation.setStartValue(1)
        self._document_cover_animation.setEndValue(0)
        self._document_cover_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._document_cover_animation.start()

    def fade_out(self):
        self._document_cover_animation = QPropertyAnimation(self._document_cover, b"opacity")

        self._document_cover_animation.setDuration(1000)
        self._document_cover_animation.setStartValue(0)
        self._document_cover_animation.setEndValue(1)
        self._document_cover_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._document_cover_animation.start()

    def _redraw_scene(self):
        self.viewport().update()

    def resizeEvent(self, resize_event):
        self.fitInView(QRectF(0, 0, self.w, self.h), Qt.KeepAspectRatio)

    def _calc_document_height(self, line_height):
        return (self._linecount + 1) * line_height

    def _calc_line_height(self, font):
        metrics = QFontMetricsF(font)
        line_height = metrics.height() * self.line_height_factor
        return line_height

    def _calc_font_size(self, h):
        font_size = h // (self.lines_per_screen * self.line_height_factor * 1.4)
        return font_size


class MediaMarker(QObject):
    changed = pyqtSignal()

    def __init__(self, media_progress_widget, name, progress=0.0):
        super(MediaMarker, self).__init__()

        self._media_progress_widget = media_progress_widget
        self.name = name

        self.left = -1
        self.right = -1

        self._progress = progress
        self.text = "<MARKER TEXT>"

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self.changed.emit()

    @property
    def linecount(self):
        return len(self.text.splitlines()) + 1

    def draw(self, qp):
        size = self._media_progress_widget.size()
        w = size.width()
        h = size.height()

        pen = QPen(QColor(100, 100, 100), 1,
                   Qt.SolidLine)
        qp.setPen(pen)

        font = QFont('Serif', 10, QFont.Light)
        qp.setFont(font)

        metrics = qp.fontMetrics()
        text_width = metrics.width(self.name)
        text_height = metrics.height()

        text_left = (w - 2 - text_width) * self.progress + 1
        qp.drawText(text_left, text_height, self.name)

        left = (w - 2) * self.progress + 1

        qp.drawLine(left, text_height + 3, left, h - 4)

        if self.progress > 0.5:
            qp.drawLine(text_left, text_height + 3, left, text_height + 3)
        else:
            qp.drawLine(left, text_height + 3, text_left + text_width, text_height + 3)

        self.left = text_left
        self.right = self.left + text_width


class MediaProgressWidget(MarkerMixin, QAbstractSlider):
    _marker_type_pattern = re.compile(r"^(?:\d+\. )?(.+)$")

    def __init__(self):
        super(MediaProgressWidget, self).__init__()

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self._dragging_progress = False
        self._dragging_marker = None
        self._dragging_marker_start_x = 0
        self._dragging_marker_start_pos = 0
        self._dragging_index = -1

        self.dirty = False

    def sizeHint(self):
        return QSize(400, 35)

    def paintEvent(self, e):

        qp = QPainter()
        qp.begin(self)
        self._draw_widget(qp)
        qp.end()

    def mousePressEvent(self, event):
        if event.y() > self.size().height() - 10:
            self._dragging_progress = True
            self._update_progress(event)
        else:
            for i, marker in enumerate(self._markers):
                if marker.left <= event.x() <= marker.right:
                    self._dragging_marker = marker
                    self._dragging_marker_start_x = event.x()
                    self._dragging_marker_start_pos = marker.progress
                    self._dragging_index = i
                    break

    def mouseMoveEvent(self, event):
        if self._dragging_progress:
            self._update_progress(event)
        elif self._dragging_marker is not None:
            self._update_marker(event)

    def mouseReleaseEvent(self, event):
        self._dragging_progress = False

        if self._dragging_marker is not None:
            self._dragging_marker = None
            self.dirty = True

    def _update_progress(self, mouse_event):
        w = self.size().width()
        minimum = self.minimum()
        maximum = self.maximum()
        diff = maximum - minimum
        if diff > 0:
            self.setValue(diff * mouse_event.x() / w + minimum)
            self.sliderMoved.emit(self.value())

    def _update_marker(self, mouse_event):
        progress = self._dragging_marker_start_pos + \
                   (mouse_event.x() - self._dragging_marker_start_x) / self.size().width()
        prev_progress = self._dragging_marker.progress
        self._dragging_marker.progress = max(0.0, (min(1.0, progress)))

        if self._dragging_marker == self._markers[0]:
            for marker in self._markers[1:]:
                marker.progress = (marker.progress - prev_progress) / (1 - prev_progress) * \
                                  (1 - self._dragging_marker.progress) + self._dragging_marker.progress

        else:
            prev_marker = self._markers[self._dragging_index - 1]
            length = self._dragging_marker.progress - prev_marker.progress
            m = self._marker_type_pattern.match(self._dragging_marker.name)
            marker_type = m.group(1)

            # TODO : this assumes that there are only 2 types of markers
            prev_marker_type = None
            prev_length = None
            if self._dragging_index > 1:
                m = self._marker_type_pattern.match(prev_marker.name)
                prev_marker_type = m.group(1)

                if marker_type != prev_marker_type:
                    prev_length = prev_marker.progress - self._markers[self._dragging_index - 2].progress

            for i in range(self._dragging_index, len(self._markers) - 1):
                marker = self._markers[i + 1]
                if marker_type in marker.name:
                    marker.progress = self._markers[i].progress + length
                elif prev_marker_type is not None and prev_marker_type in marker.name:
                    marker.progress = self._markers[i].progress + prev_length

    def _markers_changed(self):
        self.repaint()

    def _draw_widget(self, qp):

        font = QFont('Serif', 7, QFont.Light)
        qp.setFont(font)

        size = self.size()
        w = size.width()
        h = size.height()

        pen = QPen(QColor(180, 180, 180), 3,
                   Qt.SolidLine)
        qp.setPen(pen)

        qp.drawLine(1, h - 5, w - 1, h - 5)

        span = self.maximum() - self.minimum()
        if span == 0:
            x = 1
        else:
            x = (w - 2) * (self.value() - self.minimum()) / span + 1

        pen = QPen(QColor(130, 130, 130), 3,
                   Qt.SolidLine)

        qp.setPen(pen)

        pen = QPen(QColor(0, 0, 0), 3,
                   Qt.SolidLine)

        qp.drawLine(1, h - 5, x, h - 5)

        qp.setPen(pen)

        qp.drawLine(x, h - 5, x, h - 5)

        #
        # qp.setPen(pen)
        # qp.setBrush(Qt.NoBrush)
        # qp.drawRect(0, 0, w-1, h-1)
        #
        # j = 0
        #
        # for i in range(step, 10*step, step):
        #
        #     qp.drawLine(i, 0, i, 5)
        #     metrics = qp.fontMetrics()
        #     fw = metrics.width(str(self.num[j]))
        #     qp.drawText(i-fw/2, h/2, str(self.num[j]))
        #     j = j + 1

        for marker in self._markers:
            marker.draw(qp)


class VideoWidget(QVideoWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        p = self.palette()
        p.setColor(QPalette.Window, Qt.black)
        self.setPalette(p)

        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        elif event.key() == Qt.Key_Enter and event.modifiers() & Qt.Key_Alt:
            self.setFullScreen(not self.isFullScreen())
            event.accept()
        else:
            super(VideoWidget, self).keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.setFullScreen(not self.isFullScreen())
        event.accept()


class PlaylistModel(QAbstractItemModel):
    Title, ColumnCount = range(2)

    def __init__(self, parent=None):
        super(PlaylistModel, self).__init__(parent)

        self.m_playlist = None

    def rowCount(self, parent=QModelIndex()):
        return self.m_playlist.mediaCount() if self.m_playlist is not None and not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return self.ColumnCount if not parent.isValid() else 0

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row,
                                column) if self.m_playlist is not None and not parent.isValid() and row >= 0 and row < self.m_playlist.mediaCount() and column >= 0 and column < self.ColumnCount else QModelIndex()

    def parent(self, child):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            if index.column() == self.Title:
                location = self.m_playlist.media(index.row()).canonicalUrl()
                return QFileInfo(location.path()).fileName()

            return self.m_data[index]

        return None

    def playlist(self):
        return self.m_playlist

    def setPlaylist(self, playlist):
        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.disconnect(
                self.beginInsertItems)
            self.m_playlist.mediaInserted.disconnect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.disconnect(
                self.beginRemoveItems)
            self.m_playlist.mediaRemoved.disconnect(self.endRemoveItems)
            self.m_playlist.mediaChanged.disconnect(self.changeItems)

        self.beginResetModel()
        self.m_playlist = playlist

        if self.m_playlist is not None:
            self.m_playlist.mediaAboutToBeInserted.connect(
                self.beginInsertItems)
            self.m_playlist.mediaInserted.connect(self.endInsertItems)
            self.m_playlist.mediaAboutToBeRemoved.connect(
                self.beginRemoveItems)
            self.m_playlist.mediaRemoved.connect(self.endRemoveItems)
            self.m_playlist.mediaChanged.connect(self.changeItems)

        self.endResetModel()

    def beginInsertItems(self, start, end):
        self.beginInsertRows(QModelIndex(), start, end)

    def endInsertItems(self):
        self.endInsertRows()

    def beginRemoveItems(self, start, end):
        self.beginRemoveRows(QModelIndex(), start, end)

    def endRemoveItems(self):
        self.endRemoveRows()

    def changeItems(self, start, end):
        self.dataChanged.emit(self.index(start, 0),
                              self.index(end, self.ColumnCount))


class PlayerControls(QWidget):
    play = pyqtSignal()
    pause = pyqtSignal()
    # stop = pyqtSignal()
    # next = pyqtSignal()
    # previous = pyqtSignal()
    changeVolume = pyqtSignal(int)

    # changeMuting = pyqtSignal(bool)
    # changeRate = pyqtSignal(float)

    def __init__(self, parent=None):
        super(PlayerControls, self).__init__(parent)

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

        controls = PlayerControls()
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

        displayLayout.addWidget(self.song_select_widget)
        displayLayout.addWidget(self.screen_select_widget)

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

        self._load_settings()

    @property
    def available_song_numbers(self):
        audios = set(
            [int(os.path.splitext(filename)[0]) for filename in os.listdir(self.audio_path) if filename[0] != '.'])
        lyrics = set(
            [int(os.path.splitext(filename)[0]) for filename in os.listdir(self.lyrics_path) if filename[0] != '.'])

        return sorted(list(audios.intersection(lyrics)))

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

    def _save_timings(self):
        if self.slider.dirty:
            with open(os.path.join(self.timings_path, "{}.json".format(self._song_number)), 'w') as f:
                json.dump([marker.progress for marker in self.markers], f, indent=2)

    def _save_settings(self):
        with open(self.settings_path, 'w') as f:
            settings = {
                'lyrics_screen': QApplication.desktop().screenNumber(self.songtext_widget),
                'control_window_position': [self.x(), self.y()],
            }

            json.dump(settings, f, indent=2)

    def _load_settings(self):
        with open(self.settings_path, 'r') as f:
            settings = json.load(f)

            if 'lyrics_screen' in settings.keys():
                self.display_lyrics_on_screen(settings['lyrics_screen'])

            if 'control_window_position' in settings.keys():
                self.move(*settings['control_window_position'])


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    QFontDatabase.addApplicationFont("font/FiraSans-Regular.otf")
    QFontDatabase.addApplicationFont("font/FiraSans-Medium.otf")
    QFontDatabase.addApplicationFont("font/FiraSans-SemiBold.otf")

    player = Player()
    player.show()

    sys.exit(app.exec_())
