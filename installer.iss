[Setup]
AppName=GeoAI Overlord Enterprise
AppVersion=2026.1
AppPublisher=GeoAI Deutschland GmbH
DefaultDirName={autopf}\GeoAI_Overlord
DefaultGroupName=GeoAI Overlord
OutputDir=C:\Users\zxc12\Desktop\GeoAI_Enterprise\Output_Installer
OutputBaseFilename=GeoAI_Overlord_2026_Setup
SetupIconFile=C:\Users\zxc12\Desktop\GeoAI_Enterprise\assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "C:\Users\zxc12\Desktop\GeoAI_Enterprise\dist\GeoAI_Overlord_2026\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\GeoAI Overlord Enterprise"; Filename: "{app}\GeoAI_Overlord_2026.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\GeoAI Overlord Enterprise"; Filename: "{app}\GeoAI_Overlord_2026.exe"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\GeoAI_Overlord_2026.exe"; Description: "{cm:LaunchProgram,GeoAI Overlord Enterprise}"; Flags: nowait postinstall skipifsilent
