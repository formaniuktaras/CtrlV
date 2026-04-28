#ifndef MyAppName
  #define MyAppName "CtrlV"
#endif

#ifndef MyAppPublisher
  #define MyAppPublisher "CtrlV Team"
#endif

#ifndef MyAppExeName
  #define MyAppExeName "CtrlV.exe"
#endif

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
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=no
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputDir={#InstallerOutputDir}
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesAssociations=no
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

#if AppIconPath != ""
SetupIconFile={#AppIconPath}
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "autostart"; Description: "Launch CtrlV when Windows starts"; GroupDescription: "Startup options:"

[Files]
Source: "{#PortableDir}\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userstartup}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Parameters: "--startup"; Tasks: autostart; WorkingDir: "{app}"

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent checked

[UninstallDelete]
; User settings/logs are preserved intentionally (AppData).
Type: files; Name: "{userstartup}\\{#MyAppName}.lnk"
