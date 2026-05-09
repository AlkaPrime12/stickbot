def calcular_cambios_mmr(resultados_partida, mmr_actuales):
    k_factor = 32
    cambios = {jugador: 0 for jugador in resultados_partida}
    jugadores = list(resultados_partida.keys())

    for i in range(len(jugadores)):
        for j in range(i + 1, len(jugadores)):
            jug_a, jug_b = jugadores[i], jugadores[j]
            res_a = 1 if resultados_partida[jug_a] > resultados_partida[jug_b] else (0 if resultados_partida[jug_a] < resultados_partida[jug_b] else 0.5)
            res_b = 1 - res_a
            exp_a = 1 / (1 + 10 ** ((mmr_actuales[jug_b] - mmr_actuales[jug_a]) / 400))
            exp_b = 1 / (1 + 10 ** ((mmr_actuales[jug_a] - mmr_actuales[jug_b]) / 400))
            cambios[jug_a] += k_factor * (res_a - exp_a)
            cambios[jug_b] += k_factor * (res_b - exp_b)

    return cambios
