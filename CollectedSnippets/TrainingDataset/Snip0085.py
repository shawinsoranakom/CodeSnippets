def backtrack(
    partial: str, open_count: int, close_count: int, n: int, result: list[str]
) -> None:
    
    if len(partial) == 2 * n:
        result.append(partial)
        return

    if open_count < n:
        backtrack(partial + "(", open_count + 1, close_count, n, result)

    if close_count < open_count:
        
        backtrack(partial + ")", open_count, close_count + 1, n, result)
