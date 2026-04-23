class WaTor:
    
    time_passed: Callable[["WaTor", int], None] | None

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.time_passed = None

        self.planet: list[list[Entity | None]] = [[None] * width for _ in range(height)]

        for _ in range(PREY_INITIAL_COUNT):
            self.add_entity(prey=True)
        for _ in range(PREDATOR_INITIAL_COUNT):
            self.add_entity(prey=False)
        self.set_planet(self.planet)

    def set_planet(self, planet: list[list[Entity | None]]) -> None:
        
        self.planet = planet
        self.width = len(planet[0])
        self.height = len(planet)

    def add_entity(self, prey: bool) -> None:
        
        while True:
            row, col = randint(0, self.height - 1), randint(0, self.width - 1)
            if self.planet[row][col] is None:
                self.planet[row][col] = Entity(prey=prey, coords=(row, col))
                return

    def get_entities(self) -> list[Entity]:
       
        return [entity for column in self.planet for entity in column if entity]

    def balance_predators_and_prey(self) -> None:
       
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

    def get_surrounding_prey(self, entity: Entity) -> list[Entity]:
      
        row, col = entity.coords
        adjacent: list[tuple[int, int]] = [
            (row - 1, col),  
            (row + 1, col),  
            (row, col - 1),  
            (row, col + 1),  
        ]

        return [
            ent
            for r, c in adjacent
            if 0 <= r < self.height
            and 0 <= c < self.width
            and (ent := self.planet[r][c]) is not None
            and ent.prey
        ]

    def move_and_reproduce(
        self, entity: Entity, direction_orders: list[Literal["N", "E", "S", "W"]]
    ) -> None:
        
        row, col = coords = entity.coords

        adjacent_squares: dict[Literal["N", "E", "S", "W"], tuple[int, int]] = {
            "N": (row - 1, col), 
            "S": (row + 1, col),  
            "W": (row, col - 1),  
            "E": (row, col + 1),  
        }
        adjacent: list[tuple[int, int]] = []
        for order in direction_orders:
            adjacent.append(adjacent_squares[order])

        for r, c in adjacent:
            if (
                0 <= r < self.height
                and 0 <= c < self.width
                and self.planet[r][c] is None
            ):
                self.planet[r][c] = entity
                self.planet[row][col] = None
                entity.coords = (r, c)
                break

        if coords != entity.coords and entity.remaining_reproduction_time <= 0:
            if len(self.get_entities()) < MAX_ENTITIES:
                self.planet[row][col] = Entity(prey=entity.prey, coords=coords)
                entity.reset_reproduction_time()
        else:
            entity.remaining_reproduction_time -= 1

    def perform_prey_actions(
        self, entity: Entity, direction_orders: list[Literal["N", "E", "S", "W"]]
    ) -> None:
       
        self.move_and_reproduce(entity, direction_orders)

    def perform_predator_actions(
        self,
        entity: Entity,
        occupied_by_prey_coords: tuple[int, int] | None,
        direction_orders: list[Literal["N", "E", "S", "W"]],
    ) -> None:
        
        assert entity.energy_value is not None  
      
        if entity.energy_value == 0:
            self.planet[entity.coords[0]][entity.coords[1]] = None
            return

        if occupied_by_prey_coords is not None:

          prey = self.planet[occupied_by_prey_coords[0]][occupied_by_prey_coords[1]]
            assert prey is not None
            prey.alive = False

            self.planet[occupied_by_prey_coords[0]][occupied_by_prey_coords[1]] = entity
            self.planet[entity.coords[0]][entity.coords[1]] = None

            entity.coords = occupied_by_prey_coords

          entity.energy_value += PREDATOR_FOOD_VALUE
        else:

            self.move_and_reproduce(entity, direction_orders)

        entity.energy_value -= 1

    def run(self, *, iteration_count: int) -> None:
        
        for iter_num in range(iteration_count):
            
            all_entities = self.get_entities()

            for __ in range(len(all_entities)):
                entity = all_entities.pop(randint(0, len(all_entities) - 1))
                if entity.alive is False:
                    continue

                directions: list[Literal["N", "E", "S", "W"]] = ["N", "E", "S", "W"]
                shuffle(directions)  

                if entity.prey:
                    self.perform_prey_actions(entity, directions)
                else:

                  surrounding_prey = self.get_surrounding_prey(entity)
                    surrounding_prey_coords = None

                    if surrounding_prey:

                      shuffle(surrounding_prey)
                        surrounding_prey_coords = surrounding_prey[0].coords

                    self.perform_predator_actions(
                        entity, surrounding_prey_coords, directions
                    )

            self.balance_predators_and_prey()

            if self.time_passed is not None:
                
                self.time_passed(self, iter_num)

