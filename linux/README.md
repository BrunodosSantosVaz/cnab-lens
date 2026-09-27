# CNABLens no Linux

O CNABLens tem um executável Linux de **arquivo único**: não precisa instalar Python, Tk nem nada.
É o mesmo programa do `.exe` do Windows, compilado do mesmo código e com as mesmas opções.

## Baixar e abrir

1. Na página de [**Releases**](https://github.com/BrunodosSantosVaz/cnab-lens/releases/latest), baixe
   o `CNABLens-vX.Y.Z-linux-x64` e o `SHA256SUMS-linux.txt` da mesma versão.
2. Na pasta onde baixou:

   ```bash
   sha256sum -c SHA256SUMS-linux.txt          # deve responder "SUCESSO" / "OK"
   chmod +x CNABLens-vX.Y.Z-linux-x64         # o download não guarda a permissão de execução
   ./CNABLens-vX.Y.Z-linux-x64
   ```

Depois do `chmod +x`, também dá para abrir com dois cliques no gerenciador de arquivos. Em alguns
(como o Nautilus, do GNOME) é preciso clicar com o botão direito e escolher **Executar como um programa**.

### Onde roda

| Requisito | Detalhe |
|-----------|---------|
| Arquitetura | x86_64 (64 bits, Intel/AMD). ARM (Raspberry Pi, Apple Silicon) não é suportado. |
| Distro | qualquer uma com **glibc 2.28 ou mais nova**: Ubuntu 20.04+, Debian 10+, Linux Mint 20+, Fedora, openSUSE, Manjaro, Arch etc. Para ver a sua: `ldd --version`. |
| Interface | X11. Em Wayland, funciona pelo XWayland, que já vem ligado no GNOME e no KDE. |

### Problemas comuns

- **"Permissão negada"**: faltou o `chmod +x`.
- **A janela não abre e aparece `no display name`**: você está num terminal sem interface gráfica
  (SSH sem `-X`, servidor).
- **A primeira abertura demora alguns segundos**: é normal. O arquivo único se descompacta numa pasta
  temporária a cada execução.
- **As fontes ficaram diferentes do Windows**: a fonte Segoe UI não existe no Linux e o sistema usa outra
  parecida. Não afeta a leitura dos arquivos.

## Compilar

O executável é gerado pelo PyInstaller. Para ele rodar em qualquer distro, a compilação acontece dentro
de um container antigo (`quay.io/pypa/manylinux_2_28_x86_64`, glibc 2.28), usando o Python 3.12 portátil
do [uv](https://docs.astral.sh/uv/), que já traz o Tk. Nada é instalado no seu sistema e o repositório não
é alterado.

**Requisito:** [Docker](https://docs.docker.com/engine/install/) (seu usuário precisa poder rodar
`docker run`).

```bash
bash linux/compilar.sh                  # versão atual (src/version.py), em build-local/
bash linux/compilar.sh v0.2.0           # a partir de uma tag (git fetch --tags antes)
bash linux/compilar.sh --saida PASTA    # outra pasta de saída
bash linux/compilar.sh --rc 2           # nome de candidata: CNABLens-vX.Y.Z-rc.2-linux-x64
bash linux/compilar.sh --help
```

Resultado: `CNABLens-vX.Y.Z-linux-x64` e o `SHA256SUMS.txt`. A primeira execução baixa a imagem do
container (cerca de 2,5 GB descompactada) e leva alguns minutos.

**Sem Docker:** `bash linux/compilar.sh --sem-docker` compila no seu próprio computador (precisa do
`uv`). O executável gerado só roda em distros com glibc **igual ou mais nova** que a da sua máquina, por
isso não serve para distribuir.

### Como funciona

| Arquivo | Papel |
|---------|-------|
| `linux/build_linux.py` | Chama o PyInstaller com as mesmas opções do `scripts/build_exe.py` do Windows (`--onefile --windowed`, `src/cnab400_reader.py`) e grava o executável com o SHA-256. Pode ser chamado direto, com um Python que tenha Tkinter e o PyInstaller. |
| `linux/compilar.sh` | Prepara o ambiente (container, uv, Python 3.12 com Tk, `requirements-build.txt`) e chama o `build_linux.py`. Com uma tag, compila o código daquela versão num `git worktree` temporário. |

As versões **oficiais** não são compiladas à mão: a esteira do GitHub gera o `.exe` e o executável Linux
na mesma release candidata e publica os dois em produção (veja [docs/processo.md](../docs/processo.md)).

## Rodar pelo código-fonte

Se preferir não usar o executável, instale o Tk da sua distro e rode direto:

```bash
sudo apt install python3-tk        # Debian, Ubuntu, Mint
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch, Manjaro

python3 src/cnab400_reader.py
```

## Segurança

O executável Linux tem o **SHA-256** publicado na Release (`SHA256SUMS-linux.txt`), mas ainda não tem
atestado de procedência nem assinatura. Se preferir, compile você mesmo com o `linux/compilar.sh`. Veja
também a [política de segurança](../SECURITY.md).
