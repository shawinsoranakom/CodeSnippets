def _radio(
        self,
        label: str,
        options: OptionSequence[T],
        index: int = 0,
        format_func: Callable[[Any], Any] = str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only args:
        disabled: bool = False,
        horizontal: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext],
    ) -> Optional[T]:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=None if index == 0 else index, key=key)
        maybe_raise_label_warnings(label, label_visibility)
        opt = ensure_indexable(options)

        if not isinstance(index, int):
            raise StreamlitAPIException(
                "Radio Value has invalid type: %s" % type(index).__name__
            )

        if len(opt) > 0 and not 0 <= index < len(opt):
            raise StreamlitAPIException(
                "Radio index must be between 0 and length of options"
            )

        radio_proto = RadioProto()
        radio_proto.label = label
        radio_proto.default = index
        radio_proto.options[:] = [str(format_func(option)) for option in opt]
        radio_proto.form_id = current_form_id(self.dg)
        radio_proto.horizontal = horizontal
        if help is not None:
            radio_proto.help = dedent(help)

        serde = RadioSerde(opt, index)

        widget_state = register_widget(
            "radio",
            radio_proto,
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
        radio_proto.disabled = disabled
        radio_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )

        if widget_state.value_changed:
            radio_proto.value = serde.serialize(widget_state.value)
            radio_proto.set_value = True

        self.dg._enqueue("radio", radio_proto)
        return widget_state.value