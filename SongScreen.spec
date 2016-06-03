# -*- mode: python -*-

block_cipher = None


a = Analysis(['player.py'],
             pathex=['/Users/maccesch/Software/songscreen'],
             binaries=None,
             datas=[
                ('font/*', 'font'),
                ('lyrics/Deutsch/*', 'lyrics/Deutsch'),
                ('lyrics/timing/*', 'lyrics/timing'),
                ('lang/*.qm', 'lang'),
                ('audio/*', 'audio'),
                ('icon.ico', ''),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SongScreen',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='SongScreen')
app = BUNDLE(coll,
             name='SongScreen.app',
             icon='icon.icns',
             bundle_identifier=None)
