; TaskbarClock - Inno Setup Script

[Setup]
AppName=TaskbarClock
AppVersion=1.0.0
AppPublisher=TaskbarClock
DefaultDirName={autopf}\TaskbarClock
DefaultGroupName=TaskbarClock
OutputDir=..\dist
OutputBaseFilename=TaskbarClock-Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\TaskbarClock.exe
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\TaskbarClock.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TaskbarClock"; Filename: "{app}\TaskbarClock.exe"
Name: "{group}\Uninstall TaskbarClock"; Filename: "{uninstallexe}"
Name: "{userstartup}\TaskbarClock"; Filename: "{app}\TaskbarClock.exe"; Tasks: startup

[Tasks]
Name: "startup"; Description: "Windows起動時に自動実行"; GroupDescription: "追加オプション:"

[Run]
Filename: "{app}\TaskbarClock.exe"; Description: "TaskbarClockを起動"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\taskbar-clock"
