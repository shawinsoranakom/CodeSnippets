def print_results(results: list[TaskResult]):
    """
    Prints the results of the benchmark tasks to the console.

    Parameters
    ----------
    results : list[TaskResult]
        A list of TaskResult objects representing the results of the benchmark tasks.

    Returns
    -------
    None
    """
    for task_result in results:
        print(f"\n--- Results for {task_result.task_name} ---")
        print(f"{task_result.task_name} ({task_result.duration:.2f}s)")
        for assertion_name, assertion_result in task_result.assertion_results.items():
            checkmark = "✅" if assertion_result else "❌"
            print(f"  {checkmark} {assertion_name}")
        print()

    success_rates = [task_result.success_rate for task_result in results]
    avg_success_rate = sum(success_rates) / len(results)

    total_time = sum(task_result.duration for task_result in results)

    correct_assertions = sum(
        sum(
            assertion_result
            for assertion_result in task_result.assertion_results.values()
        )
        for task_result in results
    )
    total_assertions = sum(
        len(task_result.assertion_results) for task_result in results
    )
    correct_tasks = [
        task_result for task_result in results if task_result.success_rate == 1
    ]

    print("--- Results ---")
    print(f"Total time: {total_time:.2f}s")
    print(f"Completely correct tasks: {len(correct_tasks)}/{len(results)}")
    print(f"Total correct assertions: {correct_assertions}/{total_assertions}")
    print(f"Average success rate: {avg_success_rate * 100}% on {len(results)} tasks")
    print("--- Results ---")
    print()