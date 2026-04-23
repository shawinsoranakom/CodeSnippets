def _checkbox(
        self,
        label: str,
        value: bool = False,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        ctx: Optional[ScriptRunContext] = None,
    ) -> bool:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(
            default_value=None if value is False else value, key=key
        )

        checkbox_proto = CheckboxProto()
        checkbox_proto.label = label
        checkbox_proto.default = bool(value)
        checkbox_proto.form_id = current_form_id(self.dg)
        if help is not None:
            checkbox_proto.help = dedent(help)

        serde = CheckboxSerde(value)

        checkbox_state = register_widget(
            "checkbox",
            checkbox_proto,
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
        checkbox_proto.disabled = disabled
        if checkbox_state.value_changed:
            checkbox_proto.value = checkbox_state.value
            checkbox_proto.set_value = True

        self.dg._enqueue("checkbox", checkbox_proto)
        return checkbox_state.value