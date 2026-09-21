# Releases (cópias das versões de produção)

Esta pasta guarda, no repositório, uma **cópia de cada versão de produção** do **CNABLens**, uma pasta
por versão:

```
releases/
└── vX.Y.Z/
    ├── CNABLens-vX.Y.Z-windows-x64.exe
    └── SHA256SUMS.txt
```

A fonte oficial de download é a página de
[**Releases**](https://github.com/BrunodosSantosVaz/cnab-lens/releases) do GitHub, onde estão todas as
versões no mesmo lugar:

- **Produção**: release marcada **Latest** (`vX.Y.Z`).
- **Homologação**: **Pre-release** `vX.Y.Z-rc.N` (release candidata). Só as versões de produção têm cópia
  aqui, para o repositório não crescer a cada build.

A cópia de uma versão é criada pela ação *Publicar em produção* (ou, no caminho manual de hotfix, pelo
workflow *Publicar release*), depois da aprovação do dono, com o **mesmo binário** da candidata que foi testada. Não edite esta pasta à mão. O histórico de mudanças de cada
versão está no [CHANGELOG](../CHANGELOG.md) e o ciclo completo em [docs/processo.md](../docs/processo.md).

## Conferindo o download

No PowerShell, dentro da pasta do arquivo:

```powershell
Get-FileHash .\CNABLens-v0.1.0-windows-x64.exe -Algorithm SHA256
```

O valor deve ser igual ao de `SHA256SUMS.txt` da mesma pasta (ou da mesma Release).

## Como uma versão nova sai

1. Com todos os PRs da sprint aprovados, a esteira cria `release/x.y.z`, mescla as tarefas e atualiza
   `src/version.py` e o `CHANGELOG.md`.
2. O push na branch gera a release candidata `vX.Y.Z-rc.N` (homologação).
3. Testada a candidata e aprovados os cartões, o dono roda **Publicar em produção** e aprova o ambiente `producao`.
4. A ação mescla o PR na `main`, promove a candidata a `vX.Y.Z` (Latest), grava a cópia aqui, encerra as
   issues e apaga as branches das tarefas (as `release/x.y.z` ficam).
