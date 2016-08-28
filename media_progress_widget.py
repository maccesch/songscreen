import re

from PyQt5.QtCore import QObject, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QPen, QColor, QFont, QPainter
from PyQt5.QtWidgets import QAbstractSlider, QSizePolicy

from marker_mixin import MarkerMixin


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
    _marker_type_verse_pattern = re.compile(r"^(?:\d+)$")

    def __init__(self):
        super(MediaProgressWidget, self).__init__()

        self.setFocusPolicy(Qt.StrongFocus)
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
        progress = max(0.0, (min(1.0, progress)))

        self._update_marker_and_adjust_following(self._dragging_marker, self._dragging_index, progress)

    def _update_marker_and_adjust_following(self, update_marker, update_marker_index, progress):
        self.dirty = True
        prev_progress = update_marker.progress
        update_marker.progress = progress
        if update_marker == self._markers[0]:
            for marker in self._markers[1:]:
                marker.progress = (marker.progress - prev_progress) / (1 - prev_progress) * \
                                  (1 - update_marker.progress) + update_marker.progress

        else:
            prev_marker = self._markers[update_marker_index - 1]
            length = update_marker.progress - prev_marker.progress
            marker_type = self._get_marker_type(update_marker.name)

            # TODO : this assumes that there are only 2 types of markers
            prev_marker_type = None
            prev_length = None
            if update_marker_index > 1:
                prev_marker_type = self._get_marker_type(prev_marker.name)

                if marker_type != prev_marker_type:
                    prev_length = prev_marker.progress - self._markers[update_marker_index - 2].progress

            for i in range(update_marker_index, len(self._markers) - 1):
                marker = self._markers[i + 1]
                next_marker_type = self._get_marker_type(marker.name)
                if marker_type == next_marker_type:
                    marker.progress = self._markers[i].progress + length
                elif prev_marker_type is not None and prev_marker_type == next_marker_type:
                    marker.progress = self._markers[i].progress + prev_length

    def _get_marker_type(self, marker_name):
        m = self._marker_type_verse_pattern.match(marker_name)
        marker_type = "verse" if m is not None else "chorus"
        return marker_type

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

    @property
    def progress(self):
        return (self.value() - self.minimum()) / (self.maximum() - self.minimum())

    def set_closest_marker_to_current_progress(self):

        if len(self.markers) == 0:
            return

        index = 0
        while index < len(self.markers)-1 and self.markers[index].progress < self.progress:
            index += 1

        if index == 0:
            self._update_marker_and_adjust_following(self.markers[0], 0, self.progress)
            return

        if abs(self.progress - self.markers[index - 1].progress) < abs(self.progress - self.markers[index].progress):
            self._update_marker_and_adjust_following(self.markers[index - 1], index - 1, self.progress)
        else:
            self._update_marker_and_adjust_following(self.markers[index], index, self.progress)
