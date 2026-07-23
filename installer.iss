[Setup]
AppName=Zaza Assistant
AppVersion=1.0
DefaultDirName={pf}\Zaza Assistant
DefaultGroupName=Zaza Assistant
UninstallDisplayIcon={app}\Zaza Assistant.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:Inno Setup Examples Output
OutputBaseFilename=ZazaAssistant_Setup

[Files]
Source: "dist\Zaza Assistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Zaza Assistant"; Filename: "{app}\Zaza Assistant.exe"
Name: "{group}\Uninstall Zaza Assistant"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Zaza Assistant"; Filename: "{app}\Zaza Assistant.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\Zaza Assistant.exe"; Description: "{cm:LaunchProgram,Zaza Assistant}"; Flags: nowait postinstall skipifsilent
