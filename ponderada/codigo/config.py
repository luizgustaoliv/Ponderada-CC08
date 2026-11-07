"""Parametros individuais e tamanho do experimento da Ponderada CC08."""

NOME = "Luiz Gustavo Borges Oliveira"
LETRAS = sum(letra.isalpha() for letra in NOME)
D1 = sum(letra.isalpha() for letra in NOME.split()[0]) % 10
D2 = LETRAS % 10
N = 3 + (D2 % 5)
TOTAL = 20_000
REPETICOES = 3
LIMITE_SEM_CONSUMO = 1.0
