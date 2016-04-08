from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFormLayout, QSpinBox, QDialog, QPushButton, QHBoxLayout, QSpacerItem, QVBoxLayout


class SettingsWidget(QDialog):

    font_size_changed = pyqtSignal(int)
    line_increment_changed = pyqtSignal(int)

    def __init__(self, settings, *args, **kwargs):
        super(SettingsWidget, self).__init__(*args, **kwargs)

        self.settings = settings

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(10)
        self.font_size_input.setMaximum(200)
        self.font_size_input.setValue(settings['font_size'])
        self.font_size_input.valueChanged.connect(self._set_font_size)

        form_layout.addRow("Schriftgröße", self.font_size_input)

        self.increment_input = QSpinBox()
        self.increment_input.setMinimum(1)
        self.increment_input.setMaximum(20)
        self.increment_input.setSingleStep(1)
        self.increment_input.setValue(settings['line_increment'])
        self.increment_input.valueChanged.connect(self._set_line_increment)

        form_layout.addRow("Scroll-Schrittgröße in Zeilen", self.increment_input)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 20, 0, 0)
        footer_layout.addStretch(1)

        self.close_button = QPushButton(text="Schließen", clicked=self.hide)

        footer_layout.addWidget(self.close_button)

        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

    def _set_font_size(self, font_size):
        self.settings['font_size'] = font_size
        self.font_size_changed.emit(font_size)

    def _set_line_increment(self, increment):
        self.settings['line_increment'] = increment
        self.line_increment_changed.emit(increment)