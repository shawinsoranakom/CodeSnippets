def set_submobjects_from_number(self, number: float | complex) -> None:
        # Create the submobject list
        self.number = number
        self.num_string = self.get_num_string(number)

        # Submob_templates will be a list of cached Tex and Text mobjects,
        # with the intent of calling .copy or .become on them
        submob_templates = list(map(self.char_to_mob, self.num_string))
        if self.show_ellipsis:
            dots = self.char_to_mob("...")
            dots.arrange(RIGHT, buff=2 * dots[0].get_width())
            submob_templates.append(dots)
        if self.unit is not None:
            submob_templates.append(self.char_to_mob(self.unit))

        # Set internals
        font_size = self.get_font_size()
        if len(submob_templates) == len(self.submobjects):
            for sm, smt in zip(self.submobjects, submob_templates):
                sm.become(smt)
                sm.scale(font_size / smt.font_size)
        else:
            self.set_submobjects([
                smt.copy().scale(font_size / smt.font_size)
                for smt in submob_templates
            ])

        digit_buff = self.digit_buff_per_font_unit * font_size
        self.arrange(RIGHT, buff=digit_buff, aligned_edge=DOWN)

        # Handle alignment of special characters
        for i, c in enumerate(self.num_string):
            if c == "–" and len(self.num_string) > i + 1:
                self[i].align_to(self[i + 1], UP)
                self[i].shift(self[i + 1].get_height() * DOWN / 2)
            elif c == ",":
                self[i].shift(self[i].get_height() * DOWN / 2)
        if self.unit and self.unit.startswith("^"):
            self[-1].align_to(self, UP)

        if self.include_background_rectangle:
            self.add_background_rectangle()