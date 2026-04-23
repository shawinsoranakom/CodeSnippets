def select_axis(axis_type, axis_values, axis_values_dropdown, csv_mode):
            axis_type = axis_type or 0  # if axle type is None set to 0

            choices = self.current_axis_options[axis_type].choices
            has_choices = choices is not None

            if has_choices:
                choices = choices()
                if csv_mode:
                    if axis_values_dropdown:
                        axis_values = list_to_csv_string(list(filter(lambda x: x in choices, axis_values_dropdown)))
                        axis_values_dropdown = []
                else:
                    if axis_values:
                        axis_values_dropdown = list(filter(lambda x: x in choices, csv_string_to_list_strip(axis_values)))
                        axis_values = ""

            return (gr.Button.update(visible=has_choices), gr.Textbox.update(visible=not has_choices or csv_mode, value=axis_values),
                    gr.update(choices=choices if has_choices else None, visible=has_choices and not csv_mode, value=axis_values_dropdown))