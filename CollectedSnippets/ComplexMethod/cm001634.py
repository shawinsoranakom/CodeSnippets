def add_component(self, path, x):
        """adds component to the registry of tracked components"""

        assert not self.finalized_ui

        def apply_field(obj, field, condition=None, init_field=None):
            key = f"{path}/{field}"

            if getattr(obj, 'custom_script_source', None) is not None:
                key = f"customscript/{obj.custom_script_source}/{key}"

            if getattr(obj, 'do_not_save_to_config', False):
                return

            saved_value = self.ui_settings.get(key, None)

            if isinstance(obj, gr.Accordion) and isinstance(x, InputAccordion) and field == 'value':
                field = 'open'

            if saved_value is None:
                self.ui_settings[key] = getattr(obj, field)
            elif condition and not condition(saved_value):
                pass
            else:
                if isinstance(obj, gr.Textbox) and field == 'value':  # due to an undesirable behavior of gr.Textbox, if you give it an int value instead of str, everything dies
                    saved_value = str(saved_value)
                elif isinstance(obj, gr.Number) and field == 'value':
                    try:
                        saved_value = float(saved_value)
                    except ValueError:
                        return

                setattr(obj, field, saved_value)
                if init_field is not None:
                    init_field(saved_value)

            if field == 'value' and key not in self.component_mapping:
                self.component_mapping[key] = obj

        if type(x) in [gr.Slider, gr.Radio, gr.Checkbox, gr.Textbox, gr.Number, gr.Dropdown, ToolButton, gr.Button] and x.visible:
            apply_field(x, 'visible')

        if type(x) == gr.Slider:
            apply_field(x, 'value')
            apply_field(x, 'minimum')
            apply_field(x, 'maximum')
            apply_field(x, 'step')

        if type(x) == gr.Radio:
            apply_field(x, 'value', lambda val: val in radio_choices(x))

        if type(x) == gr.Checkbox:
            apply_field(x, 'value')

        if type(x) == gr.Textbox:
            apply_field(x, 'value')

        if type(x) == gr.Number:
            apply_field(x, 'value')

        if type(x) == gr.Dropdown:
            def check_dropdown(val):
                choices = radio_choices(x)
                if getattr(x, 'multiselect', False):
                    return all(value in choices for value in val)
                else:
                    return val in choices

            apply_field(x, 'value', check_dropdown, getattr(x, 'init_field', None))

        if type(x) == InputAccordion:
            if hasattr(x, 'custom_script_source'):
                x.accordion.custom_script_source = x.custom_script_source
            if x.accordion.visible:
                apply_field(x.accordion, 'visible')
            apply_field(x, 'value')
            apply_field(x.accordion, 'value')

        def check_tab_id(tab_id):
            tab_items = list(filter(lambda e: isinstance(e, gr.TabItem), x.children))
            if type(tab_id) == str:
                tab_ids = [t.id for t in tab_items]
                return tab_id in tab_ids
            elif type(tab_id) == int:
                return 0 <= tab_id < len(tab_items)
            else:
                return False

        if type(x) == gr.Tabs:
            apply_field(x, 'selected', check_tab_id)