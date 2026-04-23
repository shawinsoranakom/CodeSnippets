def basic(target: str, genes: list[str], debug: bool = True) -> tuple[int, int, str]:
    if N_POPULATION < N_SELECTED:
        msg = f"{N_POPULATION} must be bigger than {N_SELECTED}"
        raise ValueError(msg)
    not_in_genes_list = sorted({c for c in target if c not in genes})
    if not_in_genes_list:
        msg = f"{not_in_genes_list} is not in genes list, evolution cannot converge"
        raise ValueError(msg)

    population = []
    for _ in range(N_POPULATION):
        population.append("".join([random.choice(genes) for i in range(len(target))]))

    generation, total_population = 0, 0

    while True:
        generation += 1
        total_population += len(population)
        population_score = [evaluate(item, target) for item in population]

        population_score = sorted(population_score, key=lambda x: x[1], reverse=True)
        if population_score[0][0] == target:
            return (generation, total_population, population_score[0][0])
          
        if debug and generation % 10 == 0:
            print(
                f"\nGeneration: {generation}"
                f"\nTotal Population:{total_population}"
                f"\nBest score: {population_score[0][1]}"
                f"\nBest string: {population_score[0][0]}"
            )
        population_best = population[: int(N_POPULATION / 3)]
        population.clear()
        population.extend(population_best)
        population_score = [
            (item, score / len(target)) for item, score in population_score
        ]

        for i in range(N_SELECTED):
            population.extend(select(population_score[int(i)], population_score, genes))
            # break the cycle.  If this check is disabled, the algorithm will take
            # forever to compute large strings, but will also calculate small strings in
            # a far fewer generations.
            if len(population) > N_POPULATION:
                break
