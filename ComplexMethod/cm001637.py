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