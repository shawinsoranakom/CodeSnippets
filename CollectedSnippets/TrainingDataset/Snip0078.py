def backtrack(
    candidates: list, path: list, answer: list, target: int, previous_index: int
) -> None:
    
    if target == 0:
        answer.append(path.copy())
    else:
        for index in range(previous_index, len(candidates)):
            if target >= candidates[index]:
                path.append(candidates[index])
                backtrack(candidates, path, answer, target - candidates[index], index)
                path.pop(len(path) - 1)
