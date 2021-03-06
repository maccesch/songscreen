from functools import partial

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton


class SongSelectWidget(QWidget):
    song_selected = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
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
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._buttons = []

    def reset(self, song_numbers):
        for b in self._buttons:
            b.setParent(None)
            b.deleteLater()

        self._buttons = []

        if song_numbers:
            if song_numbers[-1] % 10 == 0:
                max_number = song_numbers[-1]
            else:
                max_number = (song_numbers[-1] // 10 + 1) * 10

            for i in range(max(30, max_number)):
                button = QPushButton()
                button.setCheckable(True)
                button.setAutoExclusive(True)
                button.setText(str(i + 1))
                button.setEnabled(i + 1 in song_numbers)

                self.layout().addWidget(button, i // 10, i % 10)
                button.pressed.connect(partial(self.song_button_pressed, i + 1))

                self._buttons.append(button)

    def song_button_pressed(self, song_number):
        self.song_selected.emit(song_number)
