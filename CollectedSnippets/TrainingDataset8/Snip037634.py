def _time_input(
        self,
        label: str,
        value: Union[time, datetime, None] = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> time:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=value, key=key)

        maybe_raise_label_warnings(label, label_visibility)

        parsed_time: time
        if value is None:
            # Set value default.
            parsed_time = datetime.now().time().replace(second=0, microsecond=0)
        elif isinstance(value, datetime):
            parsed_time = value.time().replace(second=0, microsecond=0)
        elif isinstance(value, time):
            parsed_time = value
        else:
            raise StreamlitAPIException(
                "The type of value should be one of datetime, time or None"
            )
        del value

        time_input_proto = TimeInputProto()
        time_input_proto.label = label
        time_input_proto.default = time.strftime(parsed_time, "%H:%M")
        time_input_proto.form_id = current_form_id(self.dg)
        if help is not None:
            time_input_proto.help = dedent(help)

        serde = TimeInputSerde(parsed_time)
        widget_state = register_widget(
            "time_input",
            time_input_proto,
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
        time_input_proto.disabled = disabled
        time_input_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            time_input_proto.value = serde.serialize(widget_state.value)
            time_input_proto.set_value = True

        self.dg._enqueue("time_input", time_input_proto)
        return widget_state.value