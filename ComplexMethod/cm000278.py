def tabu_search(
    first_solution, distance_of_first_solution, dict_of_neighbours, iters, size
):
    """
    Pure implementation of Tabu search algorithm for a Travelling Salesman Problem in
    Python.

    :param first_solution: The solution for the first iteration of Tabu search using
        the redundant resolution strategy in a list.
    :param distance_of_first_solution: The total distance that Travelling Salesman will
        travel, if he follows the path in first_solution.
    :param dict_of_neighbours: Dictionary with key each node and value a list of lists
        with the neighbors of the node and the cost (distance) for each neighbor.
    :param iters: The number of iterations that Tabu search will execute.
    :param size: The size of Tabu List.
    :return best_solution_ever: The solution with the lowest distance that occurred
        during the execution of Tabu search.
    :return best_cost: The total distance that Travelling Salesman will travel, if he
        follows the path in best_solution ever.
    """
    count = 1
    solution = first_solution
    tabu_list = []
    best_cost = distance_of_first_solution
    best_solution_ever = solution

    while count <= iters:
        neighborhood = find_neighborhood(solution, dict_of_neighbours)
        index_of_best_solution = 0
        best_solution = neighborhood[index_of_best_solution]
        best_cost_index = len(best_solution) - 1

        found = False
        while not found:
            i = 0
            while i < len(best_solution):
                if best_solution[i] != solution[i]:
                    first_exchange_node = best_solution[i]
                    second_exchange_node = solution[i]
                    break
                i = i + 1

            if [first_exchange_node, second_exchange_node] not in tabu_list and [
                second_exchange_node,
                first_exchange_node,
            ] not in tabu_list:
                tabu_list.append([first_exchange_node, second_exchange_node])
                found = True
                solution = best_solution[:-1]
                cost = neighborhood[index_of_best_solution][best_cost_index]
                if cost < best_cost:
                    best_cost = cost
                    best_solution_ever = solution
            else:
                index_of_best_solution = index_of_best_solution + 1
                best_solution = neighborhood[index_of_best_solution]

        if len(tabu_list) >= size:
            tabu_list.pop(0)

        count = count + 1

    return best_solution_ever, best_cost