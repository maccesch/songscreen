import os
import json
from ebooklib import epub
from ebooklib.utils import parse_html_string
from PyQt5.QtWidgets import QWizard, QWizardPage, QFormLayout, QLineEdit, QPushButton, QFileDialog


class LanguagePage(QWizardPage):

    def __init__(self, *args, **kwargs):
        super(LanguagePage, self).__init__(*args, **kwargs)

        self.setTitle(self.tr("Language"))

        layout = QFormLayout()

        self.language = QLineEdit()

        layout.addRow(self.tr("Language as called in it's language"), self.language)

        self.setLayout(layout)

        self.registerField("language*", self.language)


class EpubsPage(QWizardPage):

    def __init__(self, *args, **kwargs):
        super(EpubsPage, self).__init__(*args, **kwargs)

        self.existing = False

        self.setTitle(self.tr("Import Songbooks"))

        self.setSubTitle(self.tr("Download the old and new songbooks as EPUB files from jw.org to import them here"))

        layout = QFormLayout()

        self.old_epub_button = QPushButton(text=self.tr("Select File..."), clicked=self._old_epub_dialog)
        self.new_epub_button = QPushButton(text=self.tr("Select File..."), clicked=self._new_epub_dialog)

        layout.addRow(self.tr("Songbook as EPUB"), self.old_epub_button)
        layout.addRow(self.tr("New Songs as EPUB"), self.new_epub_button)

        self.setLayout(layout)

        self.old_epub = ""
        self.new_epub = ""

    def isComplete(self):
        return (self.existing or self.old_epub[-5:] == ".epub" and self.new_epub[-5:] == ".epub")\
               and super(EpubsPage, self).isComplete()

    def _old_epub_dialog(self):
        self.old_epub = QFileDialog.getOpenFileName(self, self.tr("Open EPUB"), "", "EPUB (*.epub)")[0]
        if self.old_epub:
            self.old_epub_button.setText(os.path.basename(self.old_epub))
        else:
            self.old_epub_button.setText(self.tr("Select File..."))
        self.completeChanged.emit()

    def _new_epub_dialog(self):
        self.new_epub = QFileDialog.getOpenFileName(self, self.tr("Open EPUB"), "", "EPUB (*.epub)")[0]
        if self.new_epub:
            self.new_epub_button.setText(os.path.basename(self.new_epub))
        else:
            self.new_epub_button.setText(self.tr("Select File..."))
        self.completeChanged.emit()


class ImportLyricsWizard(QWizard):

    def __init__(self, lyrics_path, *args, **kwargs):
        super(ImportLyricsWizard, self).__init__(*args, **kwargs)

        self.lyrics_folder = lyrics_path

        self.addPage(LanguagePage())

        self.epubs_page = EpubsPage()
        self.addPage(self.epubs_page)

        self.setWindowTitle(self.tr("Import Lyrics Wizard"))

        self.old_language = None

    def edit_language(self, name):
        self.old_language = name
        self.setField("language", name)
        self.epubs_page.existing = True

    def open(self):
        self.old_language = None
        self.restart()
        super(ImportLyricsWizard, self).open()

    def accept(self):

        self.language = self.field("language")

        lyrics_path = os.path.join(self.lyrics_folder, self.language)

        if self.old_language:
            old_lyrics_path = os.path.join(self.lyrics_folder, self.old_language)

            os.rename(old_lyrics_path, lyrics_path)
        else:
            if not os.path.exists(lyrics_path):
                os.mkdir(lyrics_path)

        self._import_old_epub(lyrics_path)
        self._import_new_epub(lyrics_path)

        super(ImportLyricsWizard, self).accept()

        self.close()

    def _import_old_epub(self, lyrics_path):
        if not self.epubs_page.old_epub:
            return

        book = epub.read_epub(self.epubs_page.old_epub)

        for no, item in enumerate(list(filter(lambda i: isinstance(i, epub.EpubHtml), book.items))[5:], 1):
            tree = parse_html_string(item.content).getroottree()

            titles = tree.xpath("//h1/strong/text()")
            if titles:
                title = titles[0]

                markers = []
                marker = None

                for line_element in tree.xpath("//div[@class='pGroup']/*"):
                    if line_element.tag == 'p':
                        while line_element.getchildren():
                            line_element.getchildren()[0].drop_tag()

                        line_text = line_element.text

                        if "sl" in line_element.attrib['class']:
                            verse_no, line_text = line_text.split(". ", 1)
                            if marker is not None:
                                markers.append(marker)

                            marker = {
                                'name': verse_no,
                                'text': line_text,
                            }
                        else:
                            marker['text'] += "\n{}".format(line_text)

                    elif "chorus" in line_element.attrib['class']:
                        if marker is not None:
                            markers.append(marker)

                        marker = {
                            'name': line_element.getchildren()[0].text.strip().
                                    replace('(', '').replace(')', '').lower().capitalize(),
                            'text': "",
                        }

                        for chorus_line_element in line_element.getchildren()[1:]:
                            marker['text'] += "{}\n".format(chorus_line_element.text)

                        marker['text'] = marker['text'][:-1]

                markers.append(marker)

                with open(os.path.join(lyrics_path, "{}.json".format(no)), "w") as f:
                    json.dump({
                        'title': title,
                        'markers': markers,
                    }, f, indent=2)

    def _import_new_epub(self, lyrics_path):
        if not self.epubs_page.new_epub:
            return

        book = epub.read_epub(self.epubs_page.new_epub)

        for item in filter(lambda i: isinstance(i, epub.EpubHtml), book.items):
            tree = parse_html_string(item.content).getroottree()

            title = tree.xpath("//h1/strong/text()")

            if title:
                title = title[0]

                try:
                    song_no = int(tree.xpath("//head/title/text()")[0].split(" ", 1)[0])

                    markers = []
                    marker = None

                    for verse_no, verse_element in enumerate(tree.xpath("//div[@class='pGroup']/ol/li"), 1):
                        marker = {
                            'name': verse_no,
                            'text': '',
                        }
                        for line_element in verse_element.getchildren():
                            if line_element.tag == 'p' and not 'se' in line_element.attrib.get('class', ''):
                                while line_element.getchildren():
                                    line_element.getchildren()[0].drop_tag()

                                line_text = line_element.text.strip()

                                marker['text'] += "{}\n".format(line_text)

                            elif "chorus" in line_element.attrib['class']:
                                if marker is not None:
                                    marker['text'] = marker['text'][:-1]
                                    markers.append(marker)

                                marker = {
                                    'name': line_element.getchildren()[0].text.strip().
                                        replace('(', '').replace(')', '').lower().capitalize(),
                                    'text': "",
                                }

                                for chorus_line_element in line_element.getchildren()[1:]:
                                    marker['text'] += "{}\n".format(chorus_line_element.text)

                            else:
                                if marker is not None:
                                    marker['text'] = marker['text'][:-1]
                                    markers.append(marker)

                                marker = {
                                    'name': line_element.text.strip().replace('(', '').replace(')',
                                                                                               '').lower().capitalize(),
                                    'text': "",
                                }

                        marker['text'] = marker['text'][:-1]
                        markers.append(marker)

                    if markers:
                        with open(os.path.join(lyrics_path, "{}.json".format(song_no)), "w") as f:
                            json.dump({
                                'title': title,
                                'markers': markers,
                            }, f, indent=2)

                except ValueError:
                    pass

