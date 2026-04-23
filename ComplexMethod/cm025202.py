def _check_robots_and_pets() -> None:
        entities: list[LitterRobotSensorEntity] = []

        all_robots = coordinator.account.robots
        current_robots = {robot.serial for robot in all_robots}
        new_robots = current_robots - known_robots
        if new_robots:
            known_robots.update(new_robots)
            entities.extend(
                LitterRobotSensorEntity(
                    robot=robot, coordinator=coordinator, description=description
                )
                for robot in all_robots
                if robot.serial in new_robots
                for robot_type, entity_descriptions in ROBOT_SENSOR_MAP.items()
                if isinstance(robot, robot_type)
                for description in entity_descriptions
            )

        all_pets = coordinator.account.pets
        current_pets = {pet.id for pet in all_pets}
        new_pets = current_pets - known_pets
        if new_pets:
            known_pets.update(new_pets)
            entities.extend(
                LitterRobotSensorEntity(
                    robot=pet, coordinator=coordinator, description=description
                )
                for pet in all_pets
                if pet.id in new_pets
                for description in PET_SENSORS
            )

        if entities:
            async_add_entities(entities)