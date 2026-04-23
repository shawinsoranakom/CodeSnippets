def get_knee_point_memory_budget(
        self,
        knapsack_algo: Callable[
            [list[float], list[float], float], tuple[float, list[int], list[int]]
        ],
        max_mem_budget: float = 0.1,
        min_mem_budget: float = 0.001,
        iterations: int = 100,
    ) -> float:
        """
        Finds the memory budget at the knee point in the Pareto frontier.

        The knee point is defined as the point where the trade-off between
        runtime and memory usage is optimal.

        Args:
            knapsack_algo (callable): Knapsack algorithm to use for evaluation.
            max_mem_budget (float, optional): Maximum memory budget. Defaults to 0.1.
            min_mem_budget (float, optional): Minimum memory budget. Defaults to 0.001.
            iterations (int, optional): Number of memory budgets to evaluate. Defaults to 100.

        Returns:
            float: Memory budget at the knee point.
        """
        results = self.evaluate_distribution_of_results_for_knapsack_algo(
            knapsack_algo=knapsack_algo,
            memory_budget_values=[
                min_mem_budget
                + i * (max_mem_budget - min_mem_budget) / (iterations - 1)
                for i in range(iterations)
            ],
        )
        runtime_values = [
            result["percentage_of_theoretical_peak_runtime"] for result in results
        ]
        memory_values = [
            result["percentage_of_theoretical_peak_memory"] for result in results
        ]
        runtime_range = max(runtime_values) - min(runtime_values)
        memory_range = max(memory_values) - min(memory_values)
        if runtime_range == 0 or memory_range == 0:
            return max_mem_budget

        # Normalize values
        runtime_min = min(runtime_values)
        memory_min = min(memory_values)
        runtime_norm = [
            (value - runtime_min) / runtime_range for value in runtime_values
        ]
        memory_norm = [(value - memory_min) / memory_range for value in memory_values]
        # Calculate Euclidean distance
        distances = [
            (runtime_norm[i] ** 2 + memory_norm[i] ** 2) ** 0.5
            for i in range(len(runtime_norm))
        ]
        # Find the knee point(shortest distance from the origin)
        knee_index = distances.index(min(distances))
        return results[knee_index]["memory_budget"]