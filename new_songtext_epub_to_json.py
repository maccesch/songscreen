from ebooklib import epub
from ebooklib.utils import parse_html_string
import json

book = epub.read_epub("lyrics/snnw_X.epub")

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
                    'name': '{}. Strophe'.format(verse_no),
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
                            'name': line_element.text.strip().replace('(', '').replace(')', '').lower().capitalize(),
                            'text': "",
                        }

                marker['text'] = marker['text'][:-1]
                markers.append(marker)

            if markers:

                with open("lyrics/de/{}.json".format(song_no), "w") as f:
                    json.dump({
                        'title': title,
                        'markers': markers,
                    }, f, indent=2)

        except ValueError:
            pass

