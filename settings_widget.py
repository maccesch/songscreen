from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFormLayout, QSpinBox, QDialog


class SettingsWidget(QDialog):

    font_size_changed = pyqtSignal(int)

    def __init__(self, settings, *args, **kwargs):
        super(SettingsWidget, self).__init__(*args, **kwargs)

        self.settings = settings

        main_layout = QFormLayout()

        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(10)
        self.font_size_input.setMaximum(200)
        self.font_size_input.setValue(settings['font_size'])
        self.font_size_input.valueChanged.connect(self._set_font_size)

        main_layout.addRow("Schriftgröße", self.font_size_input)

        self.setLayout(main_layout)

    def _set_font_size(self, font_size):
        self.settings['font_size'] = font_size
        self.font_size_changed.emit(font_size)