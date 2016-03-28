Use `songtext_epub_to_json.py` and `new_songtext_epub_to_json.py` to import the song epubs from jw.org.

Download the AAC audio files from jw.org and rename them to `001.m4a` ... `149.m4a` and put them into the `audio` folder.

To deploy execute the following in a terminal

    pyinstaller SongScreen.spec
    
Of course you need to install [PyInstaller](http://pythonhosted.org/PyInstaller/) first.