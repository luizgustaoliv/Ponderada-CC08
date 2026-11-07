# Ponderada CC08 — Do pipeline ao deadlock

**Luiz Gustavo Borges Oliveira**

Análise da arquitetura e da concorrência de uma pulseira sensorial, com experimentos de semáforos e uma decisão de produção.

O relatório está em [ponderada/ponderada-tato.md](ponderada/ponderada-tato.md). Os parâmetros são D1 = 4, D2 = 5 e N = 3, calculados em `ponderada/codigo/config.py`.

## Execução da A4

É necessário Python 3. Não há dependências externas. Na raiz do repositório, execute:

```powershell
python ponderada/codigo/versao1.py
```

```powershell
python ponderada/codigo/versao2.py
```

```powershell
python ponderada/codigo/versao3.py
```

No Linux ou macOS, use `python3` no lugar de `python`, se necessário. No Windows, `py -3` também pode ser usado quando o launcher estiver configurado.

Cada comando já faz **três execuções de 20.000 amostras** e mostra uma tabela. As saídas também são salvas em `ponderada/img/a4_versaoX.txt` e `ponderada/img/a4_versaoX.json`, substituindo os registros daquela versão. Os prints em `ponderada/img/` são capturas das janelas de visualização desses registros reais. Se forem feitas novas execuções, confira também a tabela e os prints, pois os resultados da versão sem sincronização podem mudar.

Para visualizar a saída em uma janela após executar o teste, acrescente `--janela` ao comando. Essa opção usa tkinter, disponível na instalação padrão do Python para Windows; em algumas instalações Linux, o pacote de tkinter precisa ser instalado separadamente. O modo de terminal não depende dele.

A versão 1 usa um contador sem proteção e `sleep(0)` entre leitura e escrita. A consulta ao contador é feita por espera ativa com cessão da fatia de execução. A versão 2 usa os semáforos vazio, cheio e mutex. Na versão 3, o consumidor começa quando o produtor segura o mutex com o buffer cheio, para reproduzir uma ordem de escalonamento que causa deadlock. O supervisor marca travamento após um segundo sem consumo e encerra o processo de teste, sem destravar artificialmente os semáforos.

Consumidas representa o número de leituras; perdidas é 20.000 menos os IDs válidos distintos recebidos; duplicadas são as ocorrências repetidas de IDs válidos além da primeira. O JSON inclui também leituras inválidas, quantidade produzida e os primeiros e últimos valores recebidos.

## Organização

| Caminho | Conteúdo |
|---|---|
| `ponderada/ponderada-tato.md` | Parte A e memorando da Parte B |
| `ponderada/codigo/` | Configuração e implementação da A4 |
| `ponderada/img/` | Prints e registros das execuções |

## Versionamento e entrega

A tag de entrega é `PONDERADA-CC08`. Ela identifica a versão final do relatório, do código e das evidências no GitHub.
