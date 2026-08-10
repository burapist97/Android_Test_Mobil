[Setup]
AppName=Android Test Otomasyon Merkezi
AppVersion=1.0
DefaultDirName={autopf}\TestOtomasyon
DefaultGroupName=Test Otomasyon Merkezi
OutputDir=Output
OutputBaseFilename=Otomasyon_Kurulum
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; GitHub Actions PyInstaller'ı çalıştırdıktan sonra oluşacak dist/arayuz klasörünü hedef alıyoruz
Source: "dist\arayuz\arayuz.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\arayuz\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Android Test Otomasyon"; Filename: "{app}\arayuz.exe"
Name: "{autodesktop}\Test Otomasyon Merkezi"; Filename: "{app}\arayuz.exe"; Tasks: desktopicon

[Run]
; 1. Adım: Dosyalar kopyalandıktan sonra Driver'ı sessizce kur (Klasör ve exe adını kendi driver'ına göre değiştir)
Filename: "{app}\platform-tools\driver_kurulum.exe"; Parameters: "/silent"; Flags: waituntilterminated runascurrentuser

; 2. Adım: Kurulum bittiğinde uygulamayı başlat
Filename: "{app}\arayuz.exe"; Description: "{cm:LaunchProgram,Android Test Otomasyon Merkezi}"; Flags: nowait postinstall skipifsilent
