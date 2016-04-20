
;--------------------------------

; The name of the installer
Name "SongScreen Installer"

; The file to write
OutFile "Install SongScreen.exe"

; The default installation directory
InstallDir $PROGRAMFILES\SongScreen

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\SongScreen" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "SongScreen (required)"

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  File /r "dist\SongScreen\*"

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\SongScreen "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SongScreen" "DisplayName" "SongScreen"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SongScreen" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SongScreen" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SongScreen" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\SongScreen"
  CreateShortCut "$SMPROGRAMS\SongScreen\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\SongScreen\SongScreen.lnk" "$INSTDIR\SongScreen.exe" "" "$INSTDIR\SongScreen.exe" 0

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SongScreen"
  DeleteRegKey HKLM SOFTWARE\SongScreen

  ; Remove directories used
  RMDir /r "$SMPROGRAMS\SongScreen"
  RMDir /r "$INSTDIR"

SectionEnd
