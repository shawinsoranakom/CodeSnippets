def solve(board: list[list[int]], row: int) -> bool:
  
    if row >= len(board):
        
        solution.append(board)
        printboard(board)
        print()
        return True
    for i in range(len(board)):
        
        if is_safe(board, row, i):
            board[row][i] = 1
            solve(board, row + 1)
            board[row][i] = 0
    return False
