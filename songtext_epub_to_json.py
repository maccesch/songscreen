from ebooklib import epub
from ebooklib.utils import parse_html_string
import json

book = epub.read_epub("lyrics/sn_X.epub")

for no, item in enumerate(list(filter(lambda i: isinstance(i, epub.EpubHtml), book.items))[5:], 1):
    tree = parse_html_string(item.content).getroottree()

    title = tree.xpath("//h1/strong/text()")[0]

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
                    'name': '{}. Strophe'.format(verse_no),
                    'text': line_text,
                }
            else:
                marker['text'] += "\n{}".format(line_text)

        elif "chorus" in line_element.attrib['class']:
            if marker is not None:
                markers.append(marker)

            marker = {
                'name': "Refrain",
                'text': "",
            }

            for chorus_line_element in line_element.getchildren()[1:]:
                marker['text'] += "{}\n".format(chorus_line_element.text)

            marker['text'] = marker['text'][:-1]

    markers.append(marker)

    with open("lyrics/de/{}.json".format(no), "w") as f:
        json.dump({
            'title': title,
            'markers': markers,
        }, f, indent=2)