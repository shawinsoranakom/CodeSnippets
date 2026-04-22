def _date_input(
        self,
        label: str,
        value: DateValue = None,
        min_value: SingleDateValue = None,
        max_value: SingleDateValue = None,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> DateWidgetReturn:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=value, key=key)

        maybe_raise_label_warnings(label, label_visibility)

        parsed_values = _DateInputValues.from_raw_values(
            value=value,
            min_value=min_value,
            max_value=max_value,
        )
        del value, min_value, max_value

        date_input_proto = DateInputProto()
        date_input_proto.is_range = parsed_values.is_range
        if help is not None:
            date_input_proto.help = dedent(help)

        date_input_proto.label = label
        date_input_proto.default[:] = [
            date.strftime(v, "%Y/%m/%d") for v in parsed_values.value
        ]

        date_input_proto.min = date.strftime(parsed_values.min, "%Y/%m/%d")
        date_input_proto.max = date.strftime(parsed_values.max, "%Y/%m/%d")

        date_input_proto.form_id = current_form_id(self.dg)

        serde = DateInputSerde(parsed_values)

        widget_state = register_widget(
            "date_input",
            date_input_proto,
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
        date_input_proto.disabled = disabled
        date_input_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            date_input_proto.value[:] = serde.serialize(widget_state.value)
            date_input_proto.set_value = True

        self.dg._enqueue("date_input", date_input_proto)
        return widget_state.value