[Setup]
AppName=GeoAI Overlord Enterprise
AppVersion=2026.1
AppPublisher=GeoAI Deutschland GmbH
AppPublisherURL=https://geoai-overlord.de
DefaultDirName={autopf}\GeoAI Overlord Enterprise
DefaultGroupName=GeoAI Enterprise
OutputBaseFilename=GeoAI_Overlord_2026_Setup
OutputDir=Output_Installer
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
SetupIconFile=web\app_icon.ico

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "GeoAI_Encrypted_Payload.bin"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
Source: "installer_key.bin"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
Source: "installer_stub.py"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

[Icons]
Name: "{group}\GeoAI Overlord Enterprise"; Filename: "{app}\GeoAI_Core\GeoAI_Enterprise.exe"
Name: "{autodesktop}\GeoAI Overlord Enterprise 2026"; Filename: "{app}\GeoAI_Core\GeoAI_Enterprise.exe"

[Run]
Filename: "python.exe"; Parameters: """{tmp}\installer_stub.py"" ""{app}"""; StatusMsg: "Entpacke und authentifiziere kryptografisch geschuetzte Dateien..."; Flags: runhidden waituntilterminated
Filename: "{app}\GeoAI_Core\GeoAI_Enterprise.exe"; Description: "GeoAI Overlord Enterprise jetzt starten"; Flags: postinstall nowait skipifsilent
