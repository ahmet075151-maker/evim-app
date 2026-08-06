@echo off
chcp 65001 >nul
title Evim - Ilk Kurulum (WSL1 - Sanallastirma GEREKTIRMEZ)
color 0A
echo ============================================================
echo   EVIM - ILK KURULUM (WSL SURUM 1)
echo   Bu yontem BIOS'ta sanallastirma (VT-x/AMD-V) GEREKTIRMEZ.
echo ============================================================
echo.
echo Yonetici olarak calistigimizdan emin oluyoruz...
net session >nul 2>&1
if not %errorlevel%==0 (
    echo [HATA] Bu dosyayi SAG TIKLAYIP "Yonetici olarak calistir" ile acmaniz gerekiyor.
    pause
    exit /b
)

echo [1/3] Windows'un Linux alt sistemi ozelligi aciliyor (sanallastirma gerektirmez)...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

echo.
echo [2/3] WSL varsayilan surumu 1 olarak ayarlaniyor (sanallastirma istemeyen surum)...
wsl --set-default-version 1 >nul 2>&1

echo.
echo ============================================================
echo   SIMDI BILGISAYARINIZI YENIDEN BASLATIN.
echo   Yeniden baslattiktan sonra:
echo   1) Microsoft Store'u acin, "Ubuntu" arayin, kurun (ucretsiz).
echo   2) Kurulan Ubuntu uygulamasini bir kez acin, size sorulan
echo      kullanici adi ve sifreyi belirleyin (sifre yazarken ekranda
echo      gorunmez, bu normaldir).
echo   3) Ardindan "2_APK_OLUSTUR.bat" dosyasini calistirin.
echo.
echo   NOT: Eger Microsoft Store'dan Ubuntu kurulumu da basarisiz
echo   olursa veya "sanallastirma" hatasi almaya devam ederseniz,
echo   bilgisayariniz WSL icin gerekli minimum Windows surumunu
echo   karsilamiyor olabilir. Bu durumda "BULUTTA_DERLEME_TALIMATI.txt"
echo   dosyasindaki yontemi kullanin - o yontem bilgisayarinizda
echo   HICBIR sey kurmadan, internetten APK uretir.
echo ============================================================
pause
