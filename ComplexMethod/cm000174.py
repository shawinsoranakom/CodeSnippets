def basic(target: str, genes: list[str], debug: bool = True) -> tuple[int, int, str]:
    """
    Verify that the target contains no genes besides the ones inside genes variable.

    >>> from string import ascii_lowercase
    >>> basic("doctest", ascii_lowercase, debug=False)[2]
    'doctest'
    >>> genes = list(ascii_lowercase)
    >>> genes.remove("e")
    >>> basic("test", genes)
    Traceback (most recent call last):
        ...
    ValueError: ['e'] is not in genes list, evolution cannot converge
    >>> genes.remove("s")
    >>> basic("test", genes)
    Traceback (most recent call last):
        ...
    ValueError: ['e', 's'] is not in genes list, evolution cannot converge
    >>> genes.remove("t")
    >>> basic("test", genes)
    Traceback (most recent call last):
        ...
    ValueError: ['e', 's', 't'] is not in genes list, evolution cannot converge
    """

    # Verify if N_POPULATION is bigger than N_SELECTED
    if N_POPULATION < N_SELECTED:
        msg = f"{N_POPULATION} must be bigger than {N_SELECTED}"
        raise ValueError(msg)
    # Verify that the target contains no genes besides the ones inside genes variable.
    not_in_genes_list = sorted({c for c in target if c not in genes})
    if not_in_genes_list:
        msg = f"{not_in_genes_list} is not in genes list, evolution cannot converge"
        raise ValueError(msg)

    # Generate random starting population.
    population = []
    for _ in range(N_POPULATION):
        population.append("".join([random.choice(genes) for i in range(len(target))]))

    # Just some logs to know what the algorithms is doing.
    generation, total_population = 0, 0

    # This loop will end when we find a perfect match for our target.
    while True:
        generation += 1
        total_population += len(population)

        # Random population created. Now it's time to evaluate.

        # (Option 1) Adding a bit of concurrency can make everything faster,
        #
        # import concurrent.futures
        # population_score: list[tuple[str, float]] = []
        # with concurrent.futures.ThreadPoolExecutor(
        #                                   max_workers=NUM_WORKERS) as executor:
        #     futures = {executor.submit(evaluate, item, target) for item in population}
        #     concurrent.futures.wait(futures)
        #     population_score = [item.result() for item in futures]
        #
        # but with a simple algorithm like this, it will probably be slower.
        # (Option 2) We just need to call evaluate for every item inside the population.
        population_score = [evaluate(item, target) for item in population]

        # Check if there is a matching evolution.
        population_score = sorted(population_score, key=lambda x: x[1], reverse=True)
        if population_score[0][0] == target:
            return (generation, total_population, population_score[0][0])

        # Print the best result every 10 generation.
        # Just to know that the algorithm is working.
        if debug and generation % 10 == 0:
            print(
                f"\nGeneration: {generation}"
                f"\nTotal Population:{total_population}"
                f"\nBest score: {population_score[0][1]}"
                f"\nBest string: {population_score[0][0]}"
            )

        # Flush the old population, keeping some of the best evolutions.
        # Keeping this avoid regression of evolution.
        population_best = population[: int(N_POPULATION / 3)]
        population.clear()
        population.extend(population_best)
        # Normalize population score to be between 0 and 1.
        population_score = [
            (item, score / len(target)) for item, score in population_score
        ]

        # This is selection
        for i in range(N_SELECTED):
            population.extend(select(population_score[int(i)], population_score, genes))
            # Check if the population has already reached the maximum value and if so,
            # break the cycle.  If this check is disabled, the algorithm will take
            # forever to compute large strings, but will also calculate small strings in
            # a far fewer generations.
            if len(population) > N_POPULATION:
                break