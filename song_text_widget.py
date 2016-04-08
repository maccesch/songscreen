from operator import attrgetter

from PyQt5.QtCore import Qt, QRectF, QAbstractAnimation, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont, QFontMetricsF, QTransform
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsView, QSizePolicy, QGraphicsScene

from marker_mixin import MarkerMixin


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
        self._first_lyrics_line_y = 0

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

        self._font_size = 40

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

        self._rebuild_scene()

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

        vertical_offset_bias = self._line_height - self._first_lyrics_line_y
        vertical_offset = self._scroll_progress * self._document_height

        if vertical_offset <= vertical_offset_bias:
            vertical_offset = 0
        else:
            vertical_offset = min(vertical_offset - vertical_offset_bias, self._linecount * self._line_height)

        diff = self.sceneRect().y() - vertical_offset
        if abs(diff) > self._line_height * self.scroll_lines:
            factor = -int(diff) // int(self._line_height * self.scroll_lines)
            y = self.sceneRect().y() + (self._line_height * self.scroll_lines) * factor
            y = max(0, y)
            target_rect = QRectF(0, y, self.w, self.h)

            self._animation = QPropertyAnimation(self, b"sceneRect")
            self._animation.setDuration(3000)
            self._animation.setStartValue(self.sceneRect())
            self._animation.setEndValue(target_rect)
            self._animation.setEasingCurve(QEasingCurve.InOutQuad)
            self._animation.start()
            # self.setSceneRect(QRectF(0, self.sceneRect().y() + self._line_height * self.scroll_lines, w, h))

    def _rebuild_scene(self, keep_progress=False):

        if keep_progress:
            prev_scene_rect_y = self.sceneRect().y()
            prev_document_height = self._document_height

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

        left = self.w / 50
        # title.setPos(left, self._line_height)

        def add_line(text, offset=0, font=default_font, color=default_color):
            y = self._line_height * line_index + offset + self.h * 0.1

            if line_index == 1:
                self._first_lyrics_line_y = y

            metrics = QFontMetricsF(font)
            text_width = metrics.width(text)
            max_text_width = (self.w - left - left)
            overflow = text_width - max_text_width

            text = scene.addText(text, font)
            text.setPos(left, y)
            text.setDefaultTextColor(color)

            if overflow > 0:
                text.setTransform(QTransform().scale(1.0 - overflow / max_text_width, 1.0))


        line_index = 0
        add_line(self.title, offset=- self.h * 0.05, font=title_font)

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

        scene_rect_y = 0
        if keep_progress:
            self._document_cover.setOpacity(0.0)
            scene_rect_y = prev_scene_rect_y / prev_document_height * self._document_height

        self.setSceneRect(QRectF(0, scene_rect_y, self.w, self.h))

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
        return self._font_size
        # font_size = h // (self.lines_per_screen * self.line_height_factor * 1.4)
        # return font_size

    def set_font_size(self, font_size):
        self._font_size = font_size
        self._rebuild_scene(keep_progress=True)