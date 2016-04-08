from functools import partial

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QPushButton


class ScreenSelectWidget(QWidget):
    screen_selected = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(ScreenSelectWidget, self).__init__(*args, **kwargs)

        self._active_screen = -1

        self._buttons = []


        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(QLabel(self.tr("Lyrics screen")))
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
            button.setText("{} {}{}".format(
                self.tr("Screen"),
                i + 1,
                "" if desktop.screenNumber(self) != i else " ({})".format(self.tr("this", "refers to the screen"))
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