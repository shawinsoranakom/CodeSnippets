def balance_predators_and_prey(self) -> None:
        """
        Balances predators and preys so that prey
        can not dominate the predators, blocking up
        space for them to reproduce.

        >>> wt = WaTor(WIDTH, HEIGHT)
        >>> for i in range(2000):
        ...     row, col = i // HEIGHT, i % WIDTH
        ...     wt.planet[row][col] = Entity(True, coords=(row, col))
        >>> entities = len(wt.get_entities())
        >>> wt.balance_predators_and_prey()
        >>> len(wt.get_entities()) == entities
        False
        """
        entities = self.get_entities()
        shuffle(entities)

        if len(entities) >= MAX_ENTITIES - MAX_ENTITIES / 10:
            prey = [entity for entity in entities if entity.prey]
            predators = [entity for entity in entities if not entity.prey]

            prey_count, predator_count = len(prey), len(predators)

            entities_to_purge = (
                prey[:DELETE_UNBALANCED_ENTITIES]
                if prey_count > predator_count
                else predators[:DELETE_UNBALANCED_ENTITIES]
            )
            for entity in entities_to_purge:
                self.planet[entity.coords[0]][entity.coords[1]] = None