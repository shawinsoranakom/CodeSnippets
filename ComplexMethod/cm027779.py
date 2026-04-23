def make_number_changeable(
        self,
        value: float | int | str,
        index: int = 0,
        replace_all: bool = False,
        **config,
    ) -> VMobject:
        substr = str(value)
        parts = self.select_parts(substr)
        if len(parts) == 0:
            log.warning(f"{value} not found in Tex.make_number_changeable call")
            return VMobject()
        if index > len(parts) - 1:
            log.warning(f"Requested {index}th occurance of {value}, but only {len(parts)} exist")
            return VMobject()
        if not replace_all:
            parts = [parts[index]]

        from manimlib.mobject.numbers import DecimalNumber

        decimal_mobs = []
        for part in parts:
            if "num_decimal_places" not in config:
                ndp = len(substr.split(".")[1]) if "." in substr else 0
                config["num_decimal_places"] = ndp
            decimal_mob = DecimalNumber(float(value), **config)
            decimal_mob.replace(part)
            decimal_mob.match_style(part)
            if len(part) > 1:
                self.remove(*part[1:])
            self.replace_submobject(self.submobjects.index(part[0]), decimal_mob)
            decimal_mobs.append(decimal_mob)

            # Replace substr with something that looks like a tex command. This
            # is to ensure Tex.substr_to_path_count counts it correctly.
            self.string = self.string.replace(substr, R"\decimalmob", 1)

        if replace_all:
            return VGroup(*decimal_mobs)
        return decimal_mobs[index]