def _multiselect(
        self,
        label: str,
        options: OptionSequence[T],
        default: Union[Sequence[Any], Any, None] = None,
        format_func: Callable[[Any], Any] = str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,  # keyword-only arguments:
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
        max_selections: Optional[int] = None,
    ) -> List[T]:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=default, key=key)

        opt = ensure_indexable(options)
        maybe_raise_label_warnings(label, label_visibility)

        indices = _check_and_convert_to_indices(opt, default)
        multiselect_proto = MultiSelectProto()
        multiselect_proto.label = label
        default_value: List[int] = [] if indices is None else indices
        multiselect_proto.default[:] = default_value
        multiselect_proto.options[:] = [str(format_func(option)) for option in opt]
        multiselect_proto.form_id = current_form_id(self.dg)
        multiselect_proto.max_selections = max_selections or 0
        if help is not None:
            multiselect_proto.help = dedent(help)

        serde = MultiSelectSerde(opt, default_value)

        widget_state = register_widget(
            "multiselect",
            multiselect_proto,
            user_key=key,
            on_change_handler=on_change,
            args=args,
            kwargs=kwargs,
            deserializer=serde.deserialize,
            serializer=serde.serialize,
            ctx=ctx,
        )
        default_count = _get_default_count(widget_state.value)
        if max_selections and default_count > max_selections:
            raise StreamlitAPIException(
                _get_over_max_options_message(default_count, max_selections)
            )

        # This needs to be done after register_widget because we don't want
        # the following proto fields to affect a widget's ID.
        multiselect_proto.disabled = disabled
        multiselect_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            multiselect_proto.value[:] = serde.serialize(widget_state.value)
            multiselect_proto.set_value = True

        self.dg._enqueue("multiselect", multiselect_proto)
        return widget_state.value