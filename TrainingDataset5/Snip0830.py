def select(
    parent_1: tuple[str, float],
    population_score: list[tuple[str, float]],
    genes: list[str],
) -> list[str]:
    pop = []
    child_n = int(parent_1[1] * 100) + 1
    child_n = 10 if child_n >= 10 else child_n
    for _ in range(child_n):
        parent_2 = population_score[random.randint(0, N_SELECTED)][0]

        child_1, child_2 = crossover(parent_1[0], parent_2)
        pop.append(mutate(child_1, genes))
        pop.append(mutate(child_2, genes))
    return pop
