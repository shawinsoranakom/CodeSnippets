def move_and_reproduce(
        self, entity: Entity, direction_orders: list[Literal["N", "E", "S", "W"]]
    ) -> None:
        """
        Attempts to move to an unoccupied neighbouring square
        in either of the four directions (North, South, East, West).
        If the move was successful and the `remaining_reproduction_time` is
        equal to 0, then a new prey or predator can also be created
        in the previous square.

        :param direction_orders: Ordered list (like priority queue) depicting
                            order to attempt to move. Removes any systematic
                            approach of checking neighbouring squares.

        >>> planet = [
        ... [None, None, None],
        ... [None, Entity(True, coords=(1, 1)), None],
        ... [None, None, None]
        ... ]
        >>> wt = WaTor(WIDTH, HEIGHT)
        >>> wt.set_planet(planet)
        >>> wt.move_and_reproduce(Entity(True, coords=(1, 1)), direction_orders=["N"])
        >>> wt.planet  # doctest: +NORMALIZE_WHITESPACE
        [[None, Entity(prey=True, coords=(0, 1), remaining_reproduction_time=4), None],
        [None, None, None],
        [None, None, None]]
        >>> wt.planet[0][0] = Entity(True, coords=(0, 0))
        >>> wt.move_and_reproduce(Entity(True, coords=(0, 1)),
        ... direction_orders=["N", "W", "E", "S"])
        >>> wt.planet  # doctest: +NORMALIZE_WHITESPACE
        [[Entity(prey=True, coords=(0, 0), remaining_reproduction_time=5), None,
        Entity(prey=True, coords=(0, 2), remaining_reproduction_time=4)],
        [None, None, None],
        [None, None, None]]
        >>> wt.planet[0][1] = wt.planet[0][2]
        >>> wt.planet[0][2] = None
        >>> wt.move_and_reproduce(Entity(True, coords=(0, 1)),
        ... direction_orders=["N", "W", "S", "E"])
        >>> wt.planet  # doctest: +NORMALIZE_WHITESPACE
        [[Entity(prey=True, coords=(0, 0), remaining_reproduction_time=5), None, None],
        [None, Entity(prey=True, coords=(1, 1), remaining_reproduction_time=4), None],
        [None, None, None]]

        >>> wt = WaTor(WIDTH, HEIGHT)
        >>> reproducable_entity = Entity(False, coords=(0, 1))
        >>> reproducable_entity.remaining_reproduction_time = 0
        >>> wt.planet = [[None, reproducable_entity]]
        >>> wt.move_and_reproduce(reproducable_entity,
        ... direction_orders=["N", "W", "S", "E"])
        >>> wt.planet  # doctest: +NORMALIZE_WHITESPACE
        [[Entity(prey=False, coords=(0, 0),
        remaining_reproduction_time=20, energy_value=15),
        Entity(prey=False, coords=(0, 1), remaining_reproduction_time=20,
        energy_value=15)]]
        """
        row, col = coords = entity.coords

        adjacent_squares: dict[Literal["N", "E", "S", "W"], tuple[int, int]] = {
            "N": (row - 1, col),  # North
            "S": (row + 1, col),  # South
            "W": (row, col - 1),  # West
            "E": (row, col + 1),  # East
        }
        # Weight adjacent locations
        adjacent: list[tuple[int, int]] = []
        for order in direction_orders:
            adjacent.append(adjacent_squares[order])

        for r, c in adjacent:
            if (
                0 <= r < self.height
                and 0 <= c < self.width
                and self.planet[r][c] is None
            ):
                # Move entity to empty adjacent square
                self.planet[r][c] = entity
                self.planet[row][col] = None
                entity.coords = (r, c)
                break

        # (2.) See if it possible to reproduce in previous square
        if coords != entity.coords and entity.remaining_reproduction_time <= 0:
            # Check if the entities on the planet is less than the max limit
            if len(self.get_entities()) < MAX_ENTITIES:
                # Reproduce in previous square
                self.planet[row][col] = Entity(prey=entity.prey, coords=coords)
                entity.reset_reproduction_time()
        else:
            entity.remaining_reproduction_time -= 1