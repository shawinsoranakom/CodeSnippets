def add_functionality(self, demo):
        self.submit.click(
            fn=wrap_gradio_call_no_job(lambda *args: self.run_settings(*args), extra_outputs=[gr.update()]),
            inputs=self.components,
            outputs=[self.text_settings, self.result],
        )

        for _i, k, _item in self.quicksettings_list:
            component = self.component_dict[k]
            info = opts.data_labels[k]

            if isinstance(component, gr.Textbox):
                methods = [component.submit, component.blur]
            elif hasattr(component, 'release'):
                methods = [component.release]
            else:
                methods = [component.change]

            for method in methods:
                method(
                    fn=lambda value, k=k: self.run_settings_single(value, key=k),
                    inputs=[component],
                    outputs=[component, self.text_settings],
                    show_progress=info.refresh is not None,
                )

        button_set_checkpoint = gr.Button('Change checkpoint', elem_id='change_checkpoint', visible=False)
        button_set_checkpoint.click(
            fn=lambda value, _: self.run_settings_single(value, key='sd_model_checkpoint'),
            _js="function(v){ var res = desiredCheckpointName; desiredCheckpointName = ''; return [res || v, null]; }",
            inputs=[self.component_dict['sd_model_checkpoint'], self.dummy_component],
            outputs=[self.component_dict['sd_model_checkpoint'], self.text_settings],
        )

        component_keys = [k for k in opts.data_labels.keys() if k in self.component_dict]

        def get_settings_values():
            return [get_value_for_setting(key) for key in component_keys]

        demo.load(
            fn=get_settings_values,
            inputs=[],
            outputs=[self.component_dict[k] for k in component_keys],
            queue=False,
        )