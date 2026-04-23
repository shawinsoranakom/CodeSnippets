def ui(self, is_img2img):
        self.comps = []
        self.setting_names = []
        self.infotext_fields = []
        extra_options = shared.opts.extra_options_img2img if is_img2img else shared.opts.extra_options_txt2img
        elem_id_tabname = "extra_options_" + ("img2img" if is_img2img else "txt2img")

        mapping = {k: v for v, k in infotext_utils.infotext_to_setting_name_mapping}

        with gr.Blocks() as interface:
            with gr.Accordion("Options", open=False, elem_id=elem_id_tabname) if shared.opts.extra_options_accordion and extra_options else gr.Group(elem_id=elem_id_tabname):

                row_count = math.ceil(len(extra_options) / shared.opts.extra_options_cols)

                for row in range(row_count):
                    with gr.Row():
                        for col in range(shared.opts.extra_options_cols):
                            index = row * shared.opts.extra_options_cols + col
                            if index >= len(extra_options):
                                break

                            setting_name = extra_options[index]

                            with FormColumn():
                                try:
                                    comp = ui_settings.create_setting_component(setting_name)
                                except KeyError:
                                    errors.report(f"Can't add extra options for {setting_name} in ui")
                                    continue

                            self.comps.append(comp)
                            self.setting_names.append(setting_name)

                            setting_infotext_name = mapping.get(setting_name)
                            if setting_infotext_name is not None:
                                self.infotext_fields.append((comp, setting_infotext_name))

        def get_settings_values():
            res = [ui_settings.get_value_for_setting(key) for key in self.setting_names]
            return res[0] if len(res) == 1 else res

        interface.load(fn=get_settings_values, inputs=[], outputs=self.comps, queue=False, show_progress=False)

        return self.comps