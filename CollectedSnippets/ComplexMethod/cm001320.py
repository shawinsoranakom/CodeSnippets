def create_ship_placement(self, game_id: str, placement: ShipPlacement) -> None:
        game = self.games.get(game_id)

        if not game:
            raise ValueError(f"Game with ID {game_id} not found.")
        if placement.direction not in ["horizontal", "vertical"]:
            raise ValueError("Invalid ship direction")
        if self.all_ships_placed(game):
            raise ValueError("All ships are already placed. Cannot place more ships.")

        ship_length = self.SHIP_LENGTHS.get(placement.ship_type)
        if not ship_length:
            raise ValueError(f"Invalid ship type {placement.ship_type}")

        start_row, start_col = placement.start["row"], ord(
            placement.start["column"]
        ) - ord("A")

        if start_row < 1 or start_row > 10 or start_col < 0 or start_col > 9:
            raise ValueError("Placement out of bounds")

        if placement.direction == "horizontal" and start_col + ship_length > 10:
            raise ValueError("Ship extends beyond board boundaries")
        elif placement.direction == "vertical" and start_row + ship_length > 10:
            raise ValueError("Ship extends beyond board boundaries")

        for i in range(ship_length):
            if placement.direction == "horizontal":
                if game.board.get((start_row, start_col + i)):
                    raise ValueError("Ship overlaps with another ship!")
            elif placement.direction == "vertical":
                if game.board.get((start_row + i, start_col)):
                    raise ValueError("Ship overlaps with another ship!")

        for i in range(ship_length):
            if placement.direction == "horizontal":
                game.board[(start_row, start_col + i)] = placement.ship_type
            else:
                game.board[(start_row + i, start_col)] = placement.ship_type

        game.ships.append(placement)