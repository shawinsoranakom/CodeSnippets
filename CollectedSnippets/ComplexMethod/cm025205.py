def _check_robots() -> None:
        all_robots = coordinator.account.robots
        current_robots = {robot.serial for robot in all_robots}
        new_robots = current_robots - known_robots
        if new_robots:
            known_robots.update(new_robots)
            async_add_entities(
                RobotSwitchEntity(
                    robot=robot, coordinator=coordinator, description=description
                )
                for robot in all_robots
                if robot.serial in new_robots
                for robot_type, entity_descriptions in SWITCH_MAP.items()
                if isinstance(robot, robot_type)
                for description in entity_descriptions
            )