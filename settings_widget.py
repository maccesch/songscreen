from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFormLayout, QSpinBox, QDialog, QPushButton, QHBoxLayout, QSpacerItem, QVBoxLayout

from import_lyrics_wizard import ImportLyricsWizard
from language_select_widget import LanguageSelectWidget


class SettingsWidget(QDialog):

    font_size_changed = pyqtSignal(int)
    line_increment_changed = pyqtSignal(int)
    language_changed = pyqtSignal(str)

    def __init__(self, settings, lyrics_path, *args, **kwargs):
        super(SettingsWidget, self).__init__(*args, **kwargs)

        self.settings = settings

        self.setWindowTitle(self.tr("SongScreen Settings"))

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.font_size_input = QSpinBox()
        self.font_size_input.setMinimum(10)
        self.font_size_input.setMaximum(200)
        self.font_size_input.setValue(settings['font_size'])
        self.font_size_input.valueChanged.connect(self._set_font_size)

        form_layout.addRow(self.tr("Font size"), self.font_size_input)

        self.increment_input = QSpinBox()
        self.increment_input.setMinimum(1)
        self.increment_input.setMaximum(20)
        self.increment_input.setSingleStep(1)
        self.increment_input.setValue(settings['line_increment'])
        self.increment_input.valueChanged.connect(self._set_line_increment)

        form_layout.addRow(self.tr("Scroll step size in lines"), self.increment_input)

        self.language_widget = LanguageSelectWidget(lyrics_path, self.settings['lyrics_language'])
        self.language_widget.language_changed.connect(self._language_changed)

        form_layout.addRow(self.tr("Lyrics Language"), self.language_widget)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 20, 0, 0)
        footer_layout.addStretch(1)

        self.close_button = QPushButton(text=self.tr("Close"), clicked=self.hide)

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

    def _language_changed(self, name):
        self.settings['lyrics_language'] = name
        self.language_changed.emit(name)
