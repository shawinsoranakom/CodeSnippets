def _select_slider(
        self,
        label: str,
        options: OptionSequence[T] = (),
        value: object = None,
        format_func: Callable[[Any], Any] = str,
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
        ctx: Optional[ScriptRunContext] = None,
    ) -> Union[T, Tuple[T, T]]:
        key = to_key(key)
        check_callback_rules(self.dg, on_change)
        check_session_state_rules(default_value=value, key=key)
        maybe_raise_label_warnings(label, label_visibility)
        opt = ensure_indexable(options)

        if len(opt) == 0:
            raise StreamlitAPIException("The `options` argument needs to be non-empty")

        def as_index_list(v: object) -> List[int]:
            if _is_range_value(v):
                slider_value = [index_(opt, val) for val in v]
                start, end = slider_value
                if start > end:
                    slider_value = [end, start]
                return slider_value
            else:
                # Simplify future logic by always making value a list
                try:
                    return [index_(opt, v)]
                except ValueError:
                    if value is not None:
                        raise

                    return [0]

        # Convert element to index of the elements
        slider_value = as_index_list(value)

        slider_proto = SliderProto()
        slider_proto.label = label
        slider_proto.format = "%s"
        slider_proto.default[:] = slider_value
        slider_proto.min = 0
        slider_proto.max = len(opt) - 1
        slider_proto.step = 1  # default for index changes
        slider_proto.data_type = SliderProto.INT
        slider_proto.options[:] = [str(format_func(option)) for option in opt]
        slider_proto.form_id = current_form_id(self.dg)
        if help is not None:
            slider_proto.help = dedent(help)

        serde = SelectSliderSerde(opt, slider_value, _is_range_value(value))

        widget_state = register_widget(
            "slider",
            slider_proto,
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
        slider_proto.disabled = disabled
        slider_proto.label_visibility.value = get_label_visibility_proto_value(
            label_visibility
        )
        if widget_state.value_changed:
            slider_proto.value[:] = serde.serialize(widget_state.value)
            slider_proto.set_value = True

        self.dg._enqueue("slider", slider_proto)
        return widget_state.value