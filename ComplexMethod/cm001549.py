def setup_ui(self):
        all_titles = [wrap_call(script.title, script.filename, "title") or script.filename for script in self.scripts]
        self.title_map = {title.lower(): script for title, script in zip(all_titles, self.scripts)}
        self.titles = [wrap_call(script.title, script.filename, "title") or f"{script.filename} [error]" for script in self.selectable_scripts]

        self.setup_ui_for_section(None)

        dropdown = gr.Dropdown(label="Script", elem_id="script_list", choices=["None"] + self.titles, value="None", type="index")
        self.inputs[0] = dropdown

        self.setup_ui_for_section(None, self.selectable_scripts)

        def select_script(script_index):
            if script_index is None:
                script_index = 0
            selected_script = self.selectable_scripts[script_index - 1] if script_index>0 else None

            return [gr.update(visible=selected_script == s) for s in self.selectable_scripts]

        def init_field(title):
            """called when an initial value is set from ui-config.json to show script's UI components"""

            if title == 'None':
                return

            script_index = self.titles.index(title)
            self.selectable_scripts[script_index].group.visible = True

        dropdown.init_field = init_field

        dropdown.change(
            fn=select_script,
            inputs=[dropdown],
            outputs=[script.group for script in self.selectable_scripts]
        )

        self.script_load_ctr = 0

        def onload_script_visibility(params):
            title = params.get('Script', None)
            if title:
                try:
                    title_index = self.titles.index(title)
                    visibility = title_index == self.script_load_ctr
                    self.script_load_ctr = (self.script_load_ctr + 1) % len(self.titles)
                    return gr.update(visible=visibility)
                except ValueError:
                    params['Script'] = None
                    massage = f'Cannot find Script: "{title}"'
                    print(massage)
                    gr.Warning(massage)
            return gr.update(visible=False)

        self.infotext_fields.append((dropdown, lambda x: gr.update(value=x.get('Script', 'None'))))
        self.infotext_fields.extend([(script.group, onload_script_visibility) for script in self.selectable_scripts])

        self.apply_on_before_component_callbacks()

        return self.inputs