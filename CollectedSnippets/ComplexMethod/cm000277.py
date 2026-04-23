def find_neighborhood(solution, dict_of_neighbours):
    """
    Pure implementation of generating the neighborhood (sorted by total distance of
    each solution from lowest to highest) of a solution with 1-1 exchange method, that
    means we exchange each node in a solution with each other node and generating a
    number of solution named neighborhood.

    :param solution: The solution in which we want to find the neighborhood.
    :param dict_of_neighbours: Dictionary with key each node and value a list of lists
        with the neighbors of the node and the cost (distance) for each neighbor.
    :return neighborhood_of_solution: A list that includes the solutions and the total
        distance of each solution (in form of list) that are produced with 1-1 exchange
        from the solution that the method took as an input

    Example:
    >>> find_neighborhood(['a', 'c', 'b', 'd', 'e', 'a'],
    ...                   {'a': [['b', '20'], ['c', '18'], ['d', '22'], ['e', '26']],
    ...                    'c': [['a', '18'], ['b', '10'], ['d', '23'], ['e', '24']],
    ...                    'b': [['a', '20'], ['c', '10'], ['d', '11'], ['e', '12']],
    ...                    'e': [['a', '26'], ['b', '12'], ['c', '24'], ['d', '40']],
    ...                    'd': [['a', '22'], ['b', '11'], ['c', '23'], ['e', '40']]}
    ...                   )  # doctest: +NORMALIZE_WHITESPACE
    [['a', 'e', 'b', 'd', 'c', 'a', 90],
     ['a', 'c', 'd', 'b', 'e', 'a', 90],
     ['a', 'd', 'b', 'c', 'e', 'a', 93],
     ['a', 'c', 'b', 'e', 'd', 'a', 102],
     ['a', 'c', 'e', 'd', 'b', 'a', 113],
     ['a', 'b', 'c', 'd', 'e', 'a', 119]]
    """

    neighborhood_of_solution = []

    for n in solution[1:-1]:
        idx1 = solution.index(n)
        for kn in solution[1:-1]:
            idx2 = solution.index(kn)
            if n == kn:
                continue

            _tmp = copy.deepcopy(solution)
            _tmp[idx1] = kn
            _tmp[idx2] = n

            distance = 0

            for k in _tmp[:-1]:
                next_node = _tmp[_tmp.index(k) + 1]
                for i in dict_of_neighbours[k]:
                    if i[0] == next_node:
                        distance = distance + int(i[1])
            _tmp.append(distance)

            if _tmp not in neighborhood_of_solution:
                neighborhood_of_solution.append(_tmp)

    index_of_last_item_in_the_list = len(neighborhood_of_solution[0]) - 1

    neighborhood_of_solution.sort(key=lambda x: x[index_of_last_item_in_the_list])
    return neighborhood_of_solution