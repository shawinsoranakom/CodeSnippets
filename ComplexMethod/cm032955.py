def run_functions_tuples_in_parallel(
    functions_with_args: Sequence[tuple[CallableProtocol, tuple[Any, ...]]],
    allow_failures: bool = False,
    max_workers: int | None = None,
) -> list[Any]:
    """
    Executes multiple functions in parallel and returns a list of the results for each function.
    This function preserves contextvars across threads, which is important for maintaining
    context like tenant IDs in database sessions.

    Args:
        functions_with_args: List of tuples each containing the function callable and a tuple of arguments.
        allow_failures: if set to True, then the function result will just be None
        max_workers: Max number of worker threads

    Returns:
        list: A list of results from each function, in the same order as the input functions.
    """
    workers = min(max_workers, len(functions_with_args)) if max_workers is not None else len(functions_with_args)

    if workers <= 0:
        return []

    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # The primary reason for propagating contextvars is to allow acquiring a db session
        # that respects tenant id. Context.run is expected to be low-overhead, but if we later
        # find that it is increasing latency we can make using it optional.
        future_to_index = {executor.submit(contextvars.copy_context().run, func, *args): i for i, (func, args) in enumerate(functions_with_args)}

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results.append((index, future.result()))
            except Exception as e:
                logging.exception(f"Function at index {index} failed due to {e}")
                results.append((index, None))  # type: ignore

                if not allow_failures:
                    raise

    results.sort(key=lambda x: x[0])
    return [result for index, result in results]