#define MyAppName "CtrlV"
#define MyAppPublisher "CtrlV Team"
#define MyAppExeName "CtrlV.exe"

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

#ifndef PortableDir
  #define PortableDir "..\\..\\dist\\CtrlV-portable"
#endif

#ifndef InstallerOutputDir
  #define InstallerOutputDir "..\\..\\release\\installer"
#endif

#ifndef AppIconPath
  #define AppIconPath ""
#endif

[Setup]
AppId={{D7BDB9B5-07BC-4D72-B0B7-C1E5BA7A2416}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputDir={#InstallerOutputDir}
OutputBaseFilename=CtrlV-setup-{#MyAppVersion}-x64
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=no

#if AppIconPath != ""
SetupIconFile={#AppIconPath}
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#PortableDir}\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Optional future cleanup example (disabled intentionally):
; Type: filesandordirs; Name: "{localappdata}\\CtrlV"
