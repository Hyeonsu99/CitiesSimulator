@echo off
rem Copy the latest exllu-103 build into public\preview so http://127.0.0.1:5183/?preview=103 shows it.
setlocal
set "SRC=%~dp0..\cs2-kit\projects\exllu-103\output\HighriseTower103_L1_5x4\HighriseTower103_L1_5x4"
set "DST=%~dp0public\preview"
if not exist "%DST%" mkdir "%DST%"
for %%S in (.fbx _Win.fbx _BaseColor.png _Normal.png _MaskMap.png _Emissive.png) do copy /y "%SRC%%%S" "%DST%\" >nul
echo preview files updated
