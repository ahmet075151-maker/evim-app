@echo off
chcp 65001 >nul
title Evim - APK Olusturucu
color 0B
echo ============================================================
echo   EVIM UYGULAMASI - APK OLUSTURUCU
echo   Bu islem internet hizinize gore 15-40 dakika surebilir.
echo   Lutfen pencereyi kapatmadan bekleyin.
echo ============================================================
echo.

wsl -l -v >nul 2>&1
if not %errorlevel%==0 (
    echo [HATA] WSL bulunamadi. Once "1_ILK_KURULUM.bat" dosyasini calistirin,
    echo        bilgisayarinizi yeniden baslatin, sonra bu dosyayi tekrar calistirin.
    pause
    exit /b
)

set "PROJE_YOLU=%~dp0"
set "WSL_YOL=%PROJE_YOLU:~0,1%"
set "WSL_PATH=/mnt/%WSL_YOL%%PROJE_YOLU:~2%"
set "WSL_PATH=%WSL_PATH:\=/%"

echo [1/4] Gerekli sistem paketleri kuruluyor (Java, derleyiciler vb.)...
wsl bash -c "sudo apt update -y && sudo apt install -y python3-pip python3-venv build-essential git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev automake"

echo.
echo [2/4] Buildozer ve Python kutuphaneleri kuruluyor...
wsl bash -c "pip3 install --upgrade pip buildozer cython==0.29.36 --break-system-packages 2>/dev/null || pip3 install --upgrade pip buildozer cython==0.29.36"

echo.
echo [3/4] Android SDK/NDK indiriliyor ve APK derleniyor (en uzun adim)...
wsl bash -c "cd '%WSL_PATH%' && yes | buildozer -v android debug"

echo.
echo [4/4] APK masaustune kopyalaniyor...
if not exist "%PROJE_YOLU%bin" (
    echo [HATA] Derleme basarisiz oldu, bin klasoru olusmadi. Yukaridaki hata mesajlarini kontrol edin.
    pause
    exit /b
)

copy /Y "%PROJE_YOLU%bin\*.apk" "%USERPROFILE%\Desktop\Evim.apk" >nul

echo.
echo ============================================================
if exist "%USERPROFILE%\Desktop\Evim.apk" (
    echo   TAMAMLANDI! "Evim.apk" masaustunuzde hazir.
    echo   Bu dosyayi telefonunuza aktarip kurabilirsiniz.
) else (
    echo   Bir sorun olustu, APK masaustune kopyalanamadi.
    echo   "%PROJE_YOLU%bin" klasorunu kontrol edin.
)
echo ============================================================
pause
