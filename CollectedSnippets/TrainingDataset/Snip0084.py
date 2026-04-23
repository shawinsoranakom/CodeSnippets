def solve_crossword(puzzle: list[list[str]], words: list[str]) -> bool:
    
    for row in range(len(puzzle)):
        for col in range(len(puzzle[0])):
            if puzzle[row][col] == "":
                for word in words:
                    for vertical in [True, False]:
                        if is_valid(puzzle, word, row, col, vertical):
                            place_word(puzzle, word, row, col, vertical)
                            words.remove(word)
                            if solve_crossword(puzzle, words):
                                return True
                            words.append(word)
                            remove_word(puzzle, word, row, col, vertical)
                return False
    return True
