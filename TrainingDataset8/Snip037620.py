def _text_input(
        self,
        label: str,
        value: SupportsStr = "",
        max_chars: Optional[int] = None,
        key: Optional[Key] = None,
        type: str = "default",
        help: Optional[str] = None,
        autocomplete: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        placeholder: Optional[str] = None,
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> str:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=None if value == "" else value, key=key)

        maybe_raise_label_warnings(label, label_visibility)

        text_input_proto = TextInputProto()
        text_input_proto.label = label
        text_input_proto.default = str(value)
        text_input_proto.form_id = current_form_id(self.dg)

        if help is not None:
            text_input_proto.help = dedent(help)

        if max_chars is not None:
            text_input_proto.max_chars = max_chars

        if placeholder is not None:
            text_input_proto.placeholder = str(placeholder)

        if type == "default":
            text_input_proto.type = TextInputProto.DEFAULT
        elif type == "password":
            text_input_proto.type = TextInputProto.PASSWORD
        else:
            raise StreamlitAPIException(
                "'%s' is not a valid text_input type. Valid types are 'default' and 'password'."
                % type
            )

        # Marshall the autocomplete param. If unspecified, this will be
        # set to "new-password" for password inputs.
        if autocomplete is None:
            autocomplete = "new-password" if type == "password" else ""
        text_input_proto.autocomplete = autocomplete

        serde = TextInputSerde(value)

        widget_state = register_widget(
            "text_input",
            text_input_proto,
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
        text_input_proto.disabled = disabled
        text_input_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            text_input_proto.value = widget_state.value
            text_input_proto.set_value = True

        self.dg._enqueue("text_input", text_input_proto)
        return widget_state.value