def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.snake.change_direction(0)
                elif event.key == pygame.K_DOWN:
                    self.snake.change_direction(1)
                elif event.key == pygame.K_LEFT:
                    self.snake.change_direction(2)
                elif event.key == pygame.K_RIGHT:
                    self.snake.change_direction(3)
        return True