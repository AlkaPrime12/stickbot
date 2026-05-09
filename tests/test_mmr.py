from app.domain.mmr import calcular_cambios_mmr


def test_mmr_changes_are_balanced():
    resultados = {"A": 40, "B": 30, "C": 20, "D": 10}
    mmr = {"A": 400.0, "B": 400.0, "C": 400.0, "D": 400.0}
    cambios = calcular_cambios_mmr(resultados, mmr)
    total = round(sum(cambios.values()), 6)
    assert total == 0


def test_higher_score_gets_positive_mmr():
    resultados = {"A": 50, "B": 20}
    mmr = {"A": 400.0, "B": 400.0}
    cambios = calcular_cambios_mmr(resultados, mmr)
    assert cambios["A"] > 0
    assert cambios["B"] < 0


def test_k_factor_scales_linearly():
    resultados = {"A": 50, "B": 20}
    mmr = {"A": 400.0, "B": 400.0}
    c16 = calcular_cambios_mmr(resultados, mmr, k_factor=16.0)
    c32 = calcular_cambios_mmr(resultados, mmr, k_factor=32.0)
    assert abs(c32["A"] - 2 * c16["A"]) < 1e-6
