def apply_infotext(self, request, tabname, *, script_runner=None, mentioned_script_args=None):
        """Processes `infotext` field from the `request`, and sets other fields of the `request` according to what's in infotext.

        If request already has a field set, and that field is encountered in infotext too, the value from infotext is ignored.

        Additionally, fills `mentioned_script_args` dict with index: value pairs for script arguments read from infotext.
        """

        if not request.infotext:
            return {}

        possible_fields = infotext_utils.paste_fields[tabname]["fields"]
        set_fields = request.model_dump(exclude_unset=True) if hasattr(request, "request") else request.dict(exclude_unset=True)  # pydantic v1/v2 have different names for this
        params = infotext_utils.parse_generation_parameters(request.infotext)

        def get_field_value(field, params):
            value = field.function(params) if field.function else params.get(field.label)
            if value is None:
                return None

            if field.api in request.__fields__:
                target_type = request.__fields__[field.api].type_
            else:
                target_type = type(field.component.value)

            if target_type == type(None):
                return None

            if isinstance(value, dict) and value.get('__type__') == 'generic_update':  # this is a gradio.update rather than a value
                value = value.get('value')

            if value is not None and not isinstance(value, target_type):
                value = target_type(value)

            return value

        for field in possible_fields:
            if not field.api:
                continue

            if field.api in set_fields:
                continue

            value = get_field_value(field, params)
            if value is not None:
                setattr(request, field.api, value)

        if request.override_settings is None:
            request.override_settings = {}

        overridden_settings = infotext_utils.get_override_settings(params)
        for _, setting_name, value in overridden_settings:
            if setting_name not in request.override_settings:
                request.override_settings[setting_name] = value

        if script_runner is not None and mentioned_script_args is not None:
            indexes = {v: i for i, v in enumerate(script_runner.inputs)}
            script_fields = ((field, indexes[field.component]) for field in possible_fields if field.component in indexes)

            for field, index in script_fields:
                value = get_field_value(field, params)

                if value is None:
                    continue

                mentioned_script_args[index] = value

        return params