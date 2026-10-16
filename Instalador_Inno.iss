
#define MyAppName "GenSole Conversor de Palmilhas"
#define MyAppVersion "1.1.0"
#define MyAppExeName "GenSole_Conversor.exe"

[Setup]
AppId={{C3B7DBE6-A841-4CE8-A5AA-2CEB21E7B5B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\GenSole Conversor
DefaultGroupName={#MyAppName}
OutputDir=instalador_saida
OutputBaseFilename=Setup_GenSole_Conversor_1.1.0
SetupIconFile=Icone.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
