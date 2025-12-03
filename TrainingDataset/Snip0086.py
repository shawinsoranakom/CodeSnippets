def generate_parenthesis(n: int) -> list[str]:
    
    result: list[str] = []
    backtrack("", 0, 0, n, result)
    return result
