def combination_sum(candidates: list, target: int) -> list:
    
    if not candidates:
        raise ValueError("Candidates list should not be empty")

    if any(x < 0 for x in candidates):
        raise ValueError("All elements in candidates must be non-negative")

    path = [] 
    answer = []  
    backtrack(candidates, path, answer, target, 0)
    return answer
