#!/bin/bash
# Script de instalação para Linux do Sistema de Comparação de Preços

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções de utilidade
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   print_error "Este script não deve ser executado como root"
   exit 1
fi

# Verificar se Python está instalado
print_info "Verificando dependências..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 não encontrado. Por favor, instale Python 3.7 ou superior."
    exit 1
fi
print_success "Python 3 encontrado"

# Verificar versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION é muito antigo. Requerido Python 3.7 ou superior."
    exit 1
fi
print_success "Python $PYTHON_VERSION é compatível"

# Verificar Tkinter
if ! python3 -c "import tkinter" &> /dev/null; then
    print_error "Tkinter não encontrado. Por favor, instale:"
    print_info "  Ubuntu/Debian: sudo apt-get install python3-tk"
    print_info "  Fedora: sudo dnf install python3-tkinter"
    print_info "  Arch: sudo pacman -S tk"
    exit 1
fi
print_success "Tkinter encontrado"

# Instalar dependências opcionais
print_info "Instalando dependências opcionais..."
if command -v pip3 &> /dev/null; then
    pip3 install --user -r requirements.txt 2>/dev/null || print_warning "Algumas dependências opcionais não puderam ser instaladas"
    print_success "Dependências instaladas"
else
    print_warning "pip3 não encontrado. Pulando instalação de dependências opcionais"
fi

# Criar diretório de instalação
INSTALL_DIR="$HOME/.local/share/ondonto-price-desktop"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

print_info "Criando diretórios de instalação..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copiar arquivos
print_info "Copiando arquivos..."
cp main.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/" 2>/dev/null || true

# Criar script de execução
cat > "$BIN_DIR/ondonto-price-desktop" << 'EOF'
#!/bin/bash
cd "$HOME/.local/share/ondonto-price-desktop"
python3 main.py "$@"
EOF

chmod +x "$BIN_DIR/ondonto-price-desktop"

# Criar arquivo .desktop
cat > "$DESKTOP_DIR/ondonto-price-desktop.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Sistema de Comparação de Preços
Comment=Sistema para comparar preços de produtos odontológicos
Exec=$BIN_DIR/ondonto-price-desktop
Icon=applications-office
Terminal=false
Categories=Office;Finance;
EOF

chmod +x "$DESKTOP_DIR/ondonto-price-desktop.desktop"

print_success "Instalação concluída!"
print_info "O aplicativo foi instalado em: $INSTALL_DIR"
print_info "Para executar use: ondonto-price-desktop"
print_info "Ou procure no menu de aplicativos da sua distribuição"

# Verificar se o PATH inclui ~/.local/bin
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    print_warning "~/.local/bin não está no seu PATH"
    print_info "Adicione ao seu ~/.bashrc ou ~/.zshrc:"
    print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    print_info "Ou execute diretamente: $BIN_DIR/ondonto-price-desktop"
fi

echo
print_success "Sistema de Comparação de Preços instalado com sucesso!"
print_info "Para desinstalar, remova os arquivos:"
print_info "  rm -rf $INSTALL_DIR"
print_info "  rm $BIN_DIR/ondonto-price-desktop"
print_info "  rm $DESKTOP_DIR/ondonto-price-desktop.desktop"
