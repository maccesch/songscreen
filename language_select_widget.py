import os

from PyQt5.QtCore import pyqtSignal, QStandardPaths
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton

from import_lyrics_wizard import ImportLyricsWizard


class LanguageSelectWidget(QWidget):
    language_changed = pyqtSignal(str)

    def __init__(self, lyrics_path, current_language, *args, **kwargs):

        super(LanguageSelectWidget, self).__init__(*args, **kwargs)

        self.lyrics_path = QStandardPaths.locate(QStandardPaths.AppDataLocation, lyrics_path,
                                                 QStandardPaths.LocateDirectory)
        self.current_language = current_language

        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        languages = []
        for filename in os.listdir(self.lyrics_path):
            if filename != "timing" and os.path.isdir(os.path.join(self.lyrics_path, filename)):
                languages.append(filename)

        self.languages_combo_box = QComboBox()
        self.languages_combo_box.addItems(sorted(languages) + [self.tr("New Language...")])
        self.languages_combo_box.currentTextChanged.connect(self._language_changed)

        self._select_current_language()
        layout.addWidget(self.languages_combo_box)

        self.edit_button = QPushButton(text=self.tr("Edit Language..."), clicked=self._edit_current_language)
        layout.addWidget(self.edit_button)

        self.setLayout(layout)

        self.import_lyrics_wizard = ImportLyricsWizard(lyrics_path,
                                                       accepted=self._wizard_done,
                                                       rejected=self._wizard_aborted,
                                                       )

        self._editing_language = False

    def _language_changed(self, name):

        if name == self.tr("New Language..."):
            self.import_lyrics_wizard.open()
        else:
            self.current_language = name
            self.language_changed.emit(name)

    def _wizard_done(self):

        languages = [self.languages_combo_box.itemText(i) for i in range(self.languages_combo_box.count() - 1)]

        if self._editing_language:
            self._editing_language = False
            old_index = languages.index(self.current_language)
            self.languages_combo_box.removeItem(old_index)
            languages.pop(old_index)

        new_language = self.import_lyrics_wizard.language
        print("new", new_language)

        languages.append(new_language)
        languages.sort()

        index = languages.index(new_language)
        self.languages_combo_box.insertItem(index, new_language)
        self.languages_combo_box.setCurrentIndex(index)

    def _wizard_aborted(self):
        self._select_current_language()

    def _select_current_language(self):
        languages = [self.languages_combo_box.itemText(i) for i in range(self.languages_combo_box.count() - 1)]
        self.languages_combo_box.setCurrentIndex(languages.index(self.current_language))

    def _edit_current_language(self):
        self._editing_language = True
        self.import_lyrics_wizard.open()
        self.import_lyrics_wizard.edit_language(self.current_language)
