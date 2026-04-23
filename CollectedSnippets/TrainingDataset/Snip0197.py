class Entity:
 
    def __init__(self, prey: bool, coords: tuple[int, int]) -> None:
        self.prey = prey
        self.coords = coords

        self.remaining_reproduction_time = (
            PREY_REPRODUCTION_TIME if prey else PREDATOR_REPRODUCTION_TIME
        )
        self.energy_value = None if prey is True else PREDATOR_INITIAL_ENERGY_VALUE
        self.alive = True

    def reset_reproduction_time(self) -> None:
       
        self.remaining_reproduction_time = (
            PREY_REPRODUCTION_TIME if self.prey is True else PREDATOR_REPRODUCTION_TIME
        )

    def __repr__(self) -> str:
        
        repr_ = (
            f"Entity(prey={self.prey}, coords={self.coords}, "
            f"remaining_reproduction_time={self.remaining_reproduction_time}"
        )
        if self.energy_value is not None:
            repr_ += f", energy_value={self.energy_value}"
        return f"{repr_})"
