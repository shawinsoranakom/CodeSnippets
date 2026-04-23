def _text_area(
        self,
        label: str,
        value: SupportsStr = "",
        height: Optional[int] = None,
        max_chars: Optional[int] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
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

        text_area_proto = TextAreaProto()
        text_area_proto.label = label
        text_area_proto.default = str(value)
        text_area_proto.form_id = current_form_id(self.dg)

        if help is not None:
            text_area_proto.help = dedent(help)

        if height is not None:
            text_area_proto.height = height

        if max_chars is not None:
            text_area_proto.max_chars = max_chars

        if placeholder is not None:
            text_area_proto.placeholder = str(placeholder)

        serde = TextAreaSerde(value)
        widget_state = register_widget(
            "text_area",
            text_area_proto,
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
        text_area_proto.disabled = disabled
        text_area_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            text_area_proto.value = widget_state.value
            text_area_proto.set_value = True

        self.dg._enqueue("text_area", text_area_proto)
        return widget_state.value