def get_number_mobject(
        self,
        x: float,
        direction: Vect3 | None = None,
        buff: float | None = None,
        unit: float = 1.0,
        unit_tex: str = "",
        **number_config
    ) -> DecimalNumber:
        number_config = merge_dicts_recursively(
            self.decimal_number_config, number_config,
        )
        if direction is None:
            direction = self.line_to_number_direction
        if buff is None:
            buff = self.line_to_number_buff
        if unit_tex:
            number_config["unit"] = unit_tex

        num_mob = DecimalNumber(x / unit, **number_config)
        num_mob.next_to(
            self.number_to_point(x),
            direction=direction,
            buff=buff
        )
        if x < 0 and direction[0] == 0:
            # Align without the minus sign
            num_mob.shift(num_mob[0].get_width() * LEFT / 2)
        if abs(x) == unit and unit_tex:
            center = num_mob.get_center()
            if x > 0:
                num_mob.remove(num_mob[0])
            else:
                num_mob.remove(num_mob[1])
                num_mob[0].next_to(num_mob[1], LEFT, buff=num_mob[0].get_width() / 4)
            num_mob.move_to(center)
        return num_mob