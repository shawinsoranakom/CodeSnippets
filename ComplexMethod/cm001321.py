def create_turn(self, game_id: str, turn: Turn) -> TurnResponse:
        game = self.games.get(game_id)

        if not game:
            raise ValueError(f"Game with ID {game_id} not found.")

        if not self.all_ships_placed(game):
            raise ValueError("All ships must be placed before starting turns")

        target_row, target_col = turn.target["row"], ord(turn.target["column"]) - ord(
            "A"
        )
        hit_ship = game.board.get((target_row, target_col))

        game.turns.append(turn)

        if not hit_ship or hit_ship == "hit":  # if no ship or already hit
            return TurnResponse(result="miss", ship_type=None)

        ship_placement = next(sp for sp in game.ships if sp.ship_type == hit_ship)
        start_row, start_col = (
            ship_placement.start["row"],
            ord(ship_placement.start["column"]) - ord("A"),
        )
        ship_positions = [
            (
                start_row + (i if ship_placement.direction == "vertical" else 0),
                start_col + (i if ship_placement.direction == "horizontal" else 0),
            )
            for i in range(self.SHIP_LENGTHS[hit_ship])
        ]

        targeted_positions = {
            (t.target["row"], ord(t.target["column"]) - ord("A")) for t in game.turns
        }

        game.board[(target_row, target_col)] = "hit"

        if set(ship_positions).issubset(targeted_positions):
            for pos in ship_positions:
                game.board[pos] = "hit"
            return TurnResponse(result="sunk", ship_type=hit_ship)
        else:
            return TurnResponse(result="hit", ship_type=hit_ship)