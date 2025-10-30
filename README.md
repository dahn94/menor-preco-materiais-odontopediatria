# Sistema de Comparação de Preços - Odontopediatria

Um aplicativo desktop multiplataforma para comparar preços de produtos odontológicos, desenvolvido em Python com Tkinter.

## 🚀 Funcionalidades

- ✅ Cadastro de produtos com categorias específicas de odontopediatria
- ✅ Comparação de preços entre múltiplos fornecedores
- ✅ Cálculo automático de subtotal e total (incluindo frete)
- ✅ Exportação de dados para CSV
- ✅ Interface intuitiva e responsiva
- ✅ Compatibilidade total com Windows, macOS e Linux

## 📋 Requisitos

- Python 3.7 ou superior
- Tkinter (incluso na instalação padrão do Python)

## 🛠️ Instalação e Execução

### Opção 1A: Executar versão Tkinter (padrão simples)

1. Clone ou baixe este repositório
2. Instale as dependências opcionais:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o aplicativo:
   ```bash
   python main.py
   ```

### Opção 1B: Executar versão Qt (moderna, recomendada no macOS)

1. Instale as dependências (inclui PySide6):
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o aplicativo Qt:
   ```bash
   python qt_app.py
   ```
3. Vantagens:
   - UI mais moderna e nativa no macOS
   - Melhor renderização em telas Retina

### Opção 2: Criar executável

#### Para criar um executável na sua plataforma:

```bash
# (Removido) Use o workflow do GitHub para gerar .exe do Windows
```

O executável será criado na pasta `dist/`.

#### Plataformas suportadas:

- **Windows**: use o workflow do GitHub Actions para gerar `.exe`
- **macOS**: crie executável Unix localmente com PyInstaller (opcional)
- **Linux**: crie executável ELF localmente com PyInstaller (opcional)

### Opção 3: Download de executáveis pré-compilados

Você pode baixar os binários gerados automaticamente pelos workflows na aba Actions do GitHub (artefatos do job mais recente em `main`).

## 🛠️ Build via GitHub Actions (GitFlow: Homolog e Release)

1. Suba este repositório para o GitHub.
2. O workflow já está em `.github/workflows/build-exec.yml`.
   - Homolog (prerelease): roda automaticamente em push/merge para `develop` e publica uma prerelease com os binários.
   - Release: ao criar uma tag `vX.Y.Z` (ex.: `v1.0.0`) ele publica uma Release com os binários.

Como baixar:
- Homolog: merge/push em `develop` → Release (prerelease) “Homolog <run_number>” com `OdontoPrice.exe` e `OdontoPrice-macos.zip`.
- Release: criar tag `vX.Y.Z` → Release com os binários anexados.

Artefatos gerados:
- Windows: `OdontoPrice-windows` (contém `dist/OdontoPrice.exe`)
- macOS: `OdontoPrice-macos` (contém `dist/OdontoPrice-macos.zip`)

## 🖥️ Compatibilidade Multiplataforma

Este aplicativo foi projetado para funcionar perfeitamente em:

### Windows
- Windows 10 ou superior
- Interface otimizada para fontes Windows
- Suporte a caminhos de arquivo Windows
- Instalador disponível (opcional)

### macOS
- macOS 10.14 (Mojave) ou superior
- Tkinter: funciona, porém sujeito a temas do sistema
- Qt (recomendado): visual moderno, nativo e estável
- Integração com menu Quit nativo e suporte Retina

### Linux
- Ubuntu 18.04+, Fedora 30+, Debian 10+ ou superior
- Interface compatível com ambientes desktop (GNOME, KDE, XFCE)
- Suporte a caminhos Unix
- Instalação via package manager opcional

## 📁 Estrutura do Projeto

```
ondonto-price-desktop/
├── main.py              # Aplicativo principal
├── requirements.txt     # Dependências Python
├── build.py            # Script para criar executáveis
├── README.md           # Este arquivo
├── icon.ico            # Ícone Windows (opcional)
├── icon.icns           # Ícone macOS (opcional)
└── icon.png            # Ícone Linux (opcional)
```

## 🔧 Personalização

### Adicionar ícones personalizados

Para adicionar ícones ao executável:

- **Windows**: Adicione `icon.ico` na raiz do projeto
- **macOS**: Adicione `icon.icns` na raiz do projeto  
- **Linux**: Adicione `icon.png` na raiz do projeto

### Modificar categorias de produtos

Edite o arquivo `main.py` e localize a lista de categorias no método `criar_interface()`:

```python
values=[
    "Biossegurança", "Semiologia", "Preventiva", "Radiologia",
    "Odontopediatria", "Isolamento Absoluto", "Dentística",
    "Moldagem e Prótese", "Endodontia", "Cirurgia", "Ortodontia"
]
```

## 🐛 Solução de Problemas

### Problemas comuns:

**Tkinter não encontrado:**
- Linux: `sudo apt-get install python3-tk` (Ubuntu/Debian)
- Fedora: `sudo dnf install python3-tkinter`

**Problemas com fontes:**
- O aplicativo ajusta automaticamente o tamanho das fontes para cada plataforma
- Se necessário, modifique o método `get_font()` em `main.py`

**Permissões negadas (Linux/macOS):**
```bash
chmod +x dist/sistema-comparacao-precos
```

**Problemas com exportação CSV:**
- Verifique permissões de escrita na pasta selecionada
- O aplicativo usa codificação UTF-8 com BOM para compatibilidade com Excel

## 📝 Licença

Este projeto está sob licença MIT. Sinta-se livre para usar, modificar e distribuir.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📞 Suporte

Para suporte ou reportar bugs:

- Abra uma issue no GitHub
- Envie um e-mail para: [santana.dahn@gmail.com]

---

**Desenvolvido com ❤️ para a comunidade odontológica**
