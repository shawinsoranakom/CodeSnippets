def iter_changes(self, current_ui_settings, values):
        """
        given a dictionary with defaults from a file and current values from gradio elements, returns
        an iterator over tuples of values that are not the same between the file and the current;
        tuple contents are: path, old value, new value
        """

        for (path, component), new_value in zip(self.component_mapping.items(), values):
            old_value = current_ui_settings.get(path)

            choices = radio_choices(component)
            if isinstance(new_value, int) and choices:
                if new_value >= len(choices):
                    continue

                new_value = choices[new_value]
                if isinstance(new_value, tuple):
                    new_value = new_value[0]

            if new_value == old_value:
                continue

            if old_value is None and new_value == '' or new_value == []:
                continue

            yield path, old_value, new_value