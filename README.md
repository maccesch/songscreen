Download the MP3 audio files from jw.org and rename them to `001.mp3`, `002.m4a`, ... and put them into the `audio` folder.

To import the lyrics in your language download the two epubs from jw.org (the song book and the new songs). With SongScreen open click on the "Settings" button and there click "New language...". Then simply follow the instructions of the language editing assistant.

To deploy execute the following in a terminal

    pyinstaller SongScreen.spec

Of course you need to install [PyInstaller](http://pythonhosted.org/PyInstaller/) first.

To enable high resolution rendering on MacOS you have to find the Info.plist file in the application package and
add the following lines

```xml
<Key>NSHighResolutionCapable</key>
<String>True</string>
```
