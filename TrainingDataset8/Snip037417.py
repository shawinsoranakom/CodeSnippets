def _color_picker(
        self,
        label: str,
        value: Optional[str] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> str:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=value, key=key)
        maybe_raise_label_warnings(label, label_visibility)

        # set value default
        if value is None:
            value = "#000000"

        # make sure the value is a string
        if not isinstance(value, str):
            raise StreamlitAPIException(
                """
                Color Picker Value has invalid type: %s. Expects a hex string
                like '#00FFAA' or '#000'.
                """
                % type(value).__name__
            )

        # validate the value and expects a hex string
        match = re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", value)

        if not match:
            raise StreamlitAPIException(
                """
                '%s' is not a valid hex code for colors. Valid ones are like
                '#00FFAA' or '#000'.
                """
                % value
            )

        color_picker_proto = ColorPickerProto()
        color_picker_proto.label = label
        color_picker_proto.default = str(value)
        color_picker_proto.form_id = current_form_id(self.dg)
        if help is not None:
            color_picker_proto.help = dedent(help)

        serde = ColorPickerSerde(value)

        widget_state = register_widget(
            "color_picker",
            color_picker_proto,
            user_key=key,
            on_change_handler=on_change,
            args=args,
            kwargs=kwargs,
            deserializer=serde.deserialize,
            serializer=serde.serialize,
            ctx=ctx,
        )

        # This needs to be done after register_widget because we don't want
        # the following proto fields to affect a widget's ID.
        color_picker_proto.disabled = disabled
        color_picker_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            color_picker_proto.value = widget_state.value
            color_picker_proto.set_value = True

        self.dg._enqueue("color_picker", color_picker_proto)
        return widget_state.value