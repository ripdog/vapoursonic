New-Item -Path 'nsis'
$nsisDir = (get-item nsis).FullName
Invoke-WebRequest -Uri 'https://phoenixnap.dl.sourceforge.net/project/nsis/NSIS%203/3.05/nsis-3.05-setup.exe' -OutFile 'nsis-3.05-setup.exe'
ls
.\nsis-3.05-setup.exe' /S "/D=$nsisDir"
$env:PATH += ';$nsisDir'
.(get-item $env:LOCALAPPDATA\pypoetry\Cache\virtualenvs\vapoursonic-*-py3.6\Scripts\python.exe).FullName -m fbs installer