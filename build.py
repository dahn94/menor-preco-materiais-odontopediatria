#!/usr/bin/env python3
"""
Script para criar executáveis multiplataforma do Sistema de Comparação de Preços
Requer: pip install pyinstaller
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import PyInstaller
        print("✓ PyInstaller encontrado")
        return True
    except ImportError:
        print("✗ PyInstaller não encontrado. Instale com: pip install pyinstaller")
        return False

def create_executable():
    """Cria executável para a plataforma atual"""
    if not check_dependencies():
        return False
    
    system = platform.system()
    app_name = "sistema-comparacao-precos"
    
    # Limpar builds anteriores
    for build_dir in ["build", "dist"]:
        if Path(build_dir).exists():
            shutil.rmtree(build_dir)
    
    # Comandos específicos por plataforma
    if system == "Windows":
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", app_name,
            "--icon=icon.ico" if Path("icon.ico").exists() else "",
            "--add-data", "requirements.txt;.",
            "main.py"
        ]
        # Remove elemento vazio se não houver ícone
        cmd = [x for x in cmd if x]
        
    elif system == "Darwin":  # macOS
        cmd = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", app_name,
            "--icon=icon.icns" if Path("icon.icns").exists() else "",
            "--add-data", "requirements.txt:.",
            "main.py"
        ]
        # Remove elemento vazio se não houver ícone
        cmd = [x for x in cmd if x]
        
    else:  # Linux
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", app_name,
            "--icon=icon.png" if Path("icon.png").exists() else "",
            "--add-data", "requirements.txt:.",
            "main.py"
        ]
        # Remove elemento vazio se não houver ícone
        cmd = [x for x in cmd if x]
    
    print(f"Criando executável para {system}...")
    print(f"Comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Executável criado com sucesso!")
        print(f"Localização: dist/{app_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao criar executável: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def create_installer():
    """Cria instalador (apenas para Windows)"""
    if platform.system() != "Windows":
        print("Instaladores estão disponíveis apenas para Windows")
        return
    
    # Criar script NSIS básico
    nsis_script = """
!define APPNAME "Sistema de Comparação de Preços"
!define VERSION "1.0"
!define PUBLISHER "Odontopediatria"

Name "${APPNAME}"
OutFile "instalador_${APPNAME}.exe"
InstallDir "$PROGRAMFILES\\${APPNAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File "dist\\sistema-comparacao-precos.exe"
    CreateShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\sistema-comparacao-precos.exe"
    CreateShortCut "$STARTMENU\\Programs\\${APPNAME}.lnk" "$INSTDIR\\sistema-comparacao-precos.exe"
SectionEnd
"""
    
    with open("installer.nsi", "w", encoding="utf-8") as f:
        f.write(nsis_script)
    
    print("Script NSIS criado: installer.nsi")
    print("Use o NSIS para compilar o instalador")

def main():
    """Função principal"""
    print("=== Sistema de Comparação de Preços - Build Multiplataforma ===")
    print(f"Plataforma atual: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--installer":
            create_installer()
            return
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python build.py           - Cria executável")
            print("  python build.py --installer - Cria instalador (Windows)")
            return
    
    # Criar executável
    if create_executable():
        print("\n✓ Build concluído com sucesso!")
        
        # Informações adicionais
        system = platform.system()
        if system == "Windows":
            print("\nPara criar um instalador, execute: python build.py --installer")
        elif system == "Darwin":
            print("\nPara criar um .app bundle, considere usar --windowed")
        else:
            print("\nO executável está pronto para distribuição")
    else:
        print("\n✗ Falha no build. Verifique os erros acima.")

if __name__ == "__main__":
    main()
