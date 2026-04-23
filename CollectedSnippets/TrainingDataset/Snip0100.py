def printboard(board: list[list[int]]) -> None:
  
    for i in range(len(board)):
        for j in range(len(board)):
            if board[i][j] == 1:
                print("Q", end=" ")  
            else:
                print(".", end=" ")  
        print()
