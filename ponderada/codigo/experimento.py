"""Experimento produtor-consumidor com tres versoes de sincronizacao.

O buffer e as threads vivem em um processo filho por repeticao. Assim, o
supervisor pode registrar e encerrar um deadlock sem liberar travas a forca.
As tres versoes usam o mesmo volume e as mesmas regras de contagem.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
import multiprocessing as mp
from pathlib import Path
import platform
import sys
import threading
import time

from config import D1, D2, LIMITE_SEM_CONSUMO, N, NOME, REPETICOES, TOTAL


def executar_filho(versao, conexao):
    """Executa uma repeticao e envia suas metricas pelo Pipe.

    Parametros: versao (1, 2 ou 3) e conexao (extremidade de envio do Pipe).
    Retorno: None; envia um dicionario serializavel ao processo supervisor.
    Funcionamento: cria o buffer circular, inicia duas threads e observa se
    ficam um segundo sem consumo; threads bloqueadas sao encerradas junto
    com este processo, depois de registrar o resultado.
    """
    buffer = [None] * N
    escrita = 0
    leitura = 0
    ocupadas = 0
    produzidas = 0
    recebidas = []
    ultimo_consumo = time.monotonic()
    inicio = ultimo_consumo
    parar = threading.Event()
    cenario_cheio = threading.Event()
    vazio = threading.Semaphore(N)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)

    def produtor():
        """Produz IDs 0..TOTAL-1; sem parametros ou retorno.

        Na v1, atualiza o contador com leitura, yield e escrita separados.
        Na v2, reserva uma vaga antes do mutex. Na v3, inverte essa ordem.
        O evento da v3 so permite ao teste iniciar o consumidor no instante
        em que o produtor ja reteve o mutex com o buffer cheio.
        """
        nonlocal escrita, ocupadas, produzidas
        for amostra in range(TOTAL):
            if versao == 1:
                while ocupadas >= N:
                    if parar.is_set():
                        return
                    time.sleep(0)  # Polling: cede a fatia, mas testa novamente.
                if parar.is_set():
                    return
                buffer[escrita] = amostra
                escrita = (escrita + 1) % N
                anterior = ocupadas
                time.sleep(0)
                ocupadas = anterior + 1
                produzidas += 1
            else:
                if versao == 3:
                    mutex.acquire()
                    if produzidas == N:
                        cenario_cheio.set()
                    vazio.acquire()
                else:
                    vazio.acquire()
                    mutex.acquire()
                buffer[escrita] = amostra
                escrita = (escrita + 1) % N
                ocupadas += 1
                produzidas += 1
                mutex.release()
                cheio.release()

    def consumidor():
        """Tenta receber TOTAL itens e registra cada valor lido.

        Parametros: nenhum. Retorno: None. Atualiza o instante de progresso
        apos cada leitura; a v1 faz polling e as outras esperam semaforos.
        """
        nonlocal leitura, ocupadas, ultimo_consumo
        for _ in range(TOTAL):
            if versao == 1:
                while ocupadas <= 0:
                    if parar.is_set():
                        return
                    time.sleep(0)  # Espera ativa, sem notificacao de semaforo.
                if parar.is_set():
                    return
                amostra = buffer[leitura]
                leitura = (leitura + 1) % N
                anterior = ocupadas
                time.sleep(0)
                ocupadas = anterior - 1
            else:
                cheio.acquire()
                mutex.acquire()
                amostra = buffer[leitura]
                leitura = (leitura + 1) % N
                ocupadas -= 1
                mutex.release()
                vazio.release()
            recebidas.append(amostra)
            ultimo_consumo = time.monotonic()

    produtora = threading.Thread(target=produtor, daemon=True)
    consumidora = threading.Thread(target=consumidor, daemon=True)
    produtora.start()
    if versao == 3:
        if not cenario_cheio.wait(timeout=LIMITE_SEM_CONSUMO):
            raise RuntimeError("O produtor nao atingiu o cenario de buffer cheio.")
        ultimo_consumo = time.monotonic()
    consumidora.start()
    travou = False
    while produtora.is_alive() or consumidora.is_alive():
        if time.monotonic() - ultimo_consumo >= LIMITE_SEM_CONSUMO:
            travou = True
            break
        time.sleep(0.005)
    parar.set()
    if versao == 1:
        produtora.join(timeout=0.1)
        consumidora.join(timeout=0.1)
    copia = list(recebidas)
    validas = [item for item in copia if isinstance(item, int) and 0 <= item < TOTAL]
    contagem = Counter(validas)
    resultado = {
        "produzidas": produzidas,
        "consumidas": len(copia),
        "unicas_validas": len(contagem),
        "perdidas": TOTAL - len(contagem),
        "duplicadas": sum(qtd - 1 for qtd in contagem.values()),
        "invalidas": len(copia) - len(validas),
        "travou": travou,
        "ocupadas_final": ocupadas,
        "duracao_s": round(time.monotonic() - inicio, 4),
        "primeiras_leituras": copia[:15],
        "ultimas_leituras": copia[-15:],
    }
    conexao.send(resultado)
    conexao.close()


def repetir(versao):
    """Executa REPETICOES processos isolados e devolve lista de resultados.

    Parametro: versao (int de 1 a 3). Retorno: list[dict]. Cada filho tem duas
    threads e um watchdog de 1 s sem consumo. O limite externo de 120 s
    apenas identifica falhas do proprio experimento, nao conta como resultado.
    """
    resultados = []
    for numero in range(1, REPETICOES + 1):
        leitura, envio = mp.Pipe(duplex=False)
        processo = mp.Process(target=executar_filho, args=(versao, envio))
        processo.start()
        envio.close()
        if not leitura.poll(120):
            processo.terminate()
            processo.join()
            raise RuntimeError("O processo de teste nao enviou as metricas.")
        resultado = leitura.recv()
        leitura.close()
        processo.join(timeout=2)
        if processo.is_alive():
            processo.terminate()
            processo.join()
        resultado["execucao"] = numero
        resultados.append(resultado)
    return resultados


def abrir_janela(texto, versao):
    """Exibe a saida real em uma janela para capturar a evidencia.

    Parametros: texto (str da saida) e versao (int). Retorno: None. A janela
    usa somente tkinter, da biblioteca padrao, e nao altera as metricas.
    """
    import tkinter as tk
    janela = tk.Tk()
    janela.title(f"Tato CC08 - Execucao real - Versao {versao}")
    janela.geometry("1060x520+70+70")
    campo = tk.Text(janela, font=("Consolas", 12), padx=22, pady=22,
                    bg="#101820", fg="#edf2f7", wrap="none")
    campo.pack(fill="both", expand=True)
    campo.insert("1.0", texto)
    campo.configure(state="disabled")
    janela.mainloop()


def main(versao):
    """Executa tres repeticoes, imprime e salva as metricas em img/.

    Parametro: versao (int). Retorno: None. A opcao --janela tambem apresenta
    a saida em uma janela; sem essa opcao, basta Python 3 no terminal.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--janela", action="store_true",
                        help="Exibe a saida em janela depois das tres execucoes.")
    args = parser.parse_args()
    resultados = repetir(versao)
    nomes = {1: "Sem sincronizacao", 2: "Tres semaforos", 3: "Ordem trocada"}
    linhas = [
        f"TATO CC08 | VERSAO {versao} | {nomes[versao]}",
        NOME, f"D1={D1} | D2={D2} | N={N} | Amostras por execucao={TOTAL}",
        f"Ambiente: {platform.system()} | Python {platform.python_version()}",
        "", "Exec  Produzidas  Consumidas  Perdidas  Duplicadas  Invalidas  Travou",
    ]
    for r in resultados:
        linhas.append(f"{r['execucao']:>4}  {r['produzidas']:>10}  {r['consumidas']:>10}"
                      f"  {r['perdidas']:>8}  {r['duplicadas']:>10}  {r['invalidas']:>9}"
                      f"  {'Sim' if r['travou'] else 'Nao'}")
    linhas += ["", "Perdidas = 20.000 - quantidade de IDs validos distintos recebidos.",
               "Duplicadas = repeticoes alem da primeira de cada ID valido.",
               "Travou = threads pendentes e pelo menos 1 s sem consumo."]
    if versao == 3:
        linhas += ["Cenario controlado: produtor segura mutex com o buffer cheio",
                   "antes de iniciar o consumidor; preserva a ordem errada dos waits."]
    texto = "\n".join(linhas) + "\n"
    destino = Path(__file__).resolve().parents[1] / "img"
    destino.mkdir(exist_ok=True)
    (destino / f"a4_versao{versao}.txt").write_text(texto, encoding="utf-8")
    dados = {"nome": NOME, "D1": D1, "D2": D2, "N": N, "total": TOTAL,
             "versao": versao, "ambiente": platform.platform(),
             "python": sys.version, "data": datetime.now().astimezone().isoformat(),
             "resultados": resultados}
    (destino / f"a4_versao{versao}.json").write_text(
        json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(texto)
    if args.janela:
        abrir_janela(texto, versao)
