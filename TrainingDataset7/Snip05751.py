def get_action_choices(self, request, default_choices=models.BLANK_CHOICE_DASH):
        """
        Return a list of choices for use in a form object. Each choice is a
        tuple (name, description).
        """
        choices = [*default_choices]
        for func, name, description in self.get_actions(request).values():
            choice = (name, description % model_format_dict(self.opts))
            choices.append(choice)
        return choices