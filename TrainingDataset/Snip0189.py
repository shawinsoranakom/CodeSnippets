class LangtonsAnt:

    def __init__(self, width: int, height: int) -> None:
        self.board = [[True] * width for _ in range(height)]
        self.ant_position: tuple[int, int] = (width // 2, height // 2)


        self.ant_direction: int = 3

        directions = {
            0: (-1, 0),  
            1: (0, 1),  
            2: (1, 0),  
            3: (0, -1),  
        }
        x, y = self.ant_position

        if self.board[x][y] is True:
            self.ant_direction = (self.ant_direction + 1) % 4
        else:
            self.ant_direction = (self.ant_direction - 1) % 4

        move_x, move_y = directions[self.ant_direction]
        self.ant_position = (x + move_x, y + move_y)

        self.board[x][y] = not self.board[x][y]

        if display and axes:
            axes.get_xaxis().set_ticks([])
            axes.get_yaxis().set_ticks([])
            axes.imshow(self.board, cmap="gray", interpolation="nearest")

    def display(self, frames: int = 100_000) -> None:
       
        fig, ax = plt.subplots()
        self.animation = FuncAnimation(
            fig, partial(self.move_ant, ax, True), frames=frames, interval=1
        )
        plt.show()
