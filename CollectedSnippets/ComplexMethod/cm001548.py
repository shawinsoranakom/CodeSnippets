def create_script_ui_inner(self, script):
        import modules.api.models as api_models

        controls = wrap_call(script.ui, script.filename, "ui", script.is_img2img)
        script.controls = controls

        if controls is None:
            return

        script.name = wrap_call(script.title, script.filename, "title", default=script.filename).lower()

        api_args = []

        for control in controls:
            control.custom_script_source = os.path.basename(script.filename)

            arg_info = api_models.ScriptArg(label=control.label or "")

            for field in ("value", "minimum", "maximum", "step"):
                v = getattr(control, field, None)
                if v is not None:
                    setattr(arg_info, field, v)

            choices = getattr(control, 'choices', None)  # as of gradio 3.41, some items in choices are strings, and some are tuples where the first elem is the string
            if choices is not None:
                arg_info.choices = [x[0] if isinstance(x, tuple) else x for x in choices]

            api_args.append(arg_info)

        script.api_info = api_models.ScriptInfo(
            name=script.name,
            is_img2img=script.is_img2img,
            is_alwayson=script.alwayson,
            args=api_args,
        )

        if script.infotext_fields is not None:
            self.infotext_fields += script.infotext_fields

        if script.paste_field_names is not None:
            self.paste_field_names += script.paste_field_names

        self.inputs += controls
        script.args_to = len(self.inputs)