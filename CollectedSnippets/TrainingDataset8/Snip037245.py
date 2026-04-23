def create_instance(
        self,
        *args,
        default: Any = None,
        key: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """Create a new instance of the component.

        Parameters
        ----------
        *args
            Must be empty; all args must be named. (This parameter exists to
            enforce correct use of the function.)
        default: any or None
            The default return value for the component. This is returned when
            the component's frontend hasn't yet specified a value with
            `setComponentValue`.
        key: str or None
            If not None, this is the user key we use to generate the
            component's "widget ID".
        **kwargs
            Keyword args to pass to the component.

        Returns
        -------
        any or None
            The component's widget value.

        """
        if len(args) > 0:
            raise MarshallComponentException(f"Argument '{args[0]}' needs a label")

        try:
            import pyarrow

            from streamlit.components.v1 import component_arrow
        except ImportError:
            raise StreamlitAPIException(
                """To use Custom Components in Streamlit, you need to install
PyArrow. To do so locally:

`pip install pyarrow`

And if you're using Streamlit Cloud, add "pyarrow" to your requirements.txt."""
            )

        # In addition to the custom kwargs passed to the component, we also
        # send the special 'default' and 'key' params to the component
        # frontend.
        all_args = dict(kwargs, **{"default": default, "key": key})

        json_args = {}
        special_args = []
        for arg_name, arg_val in all_args.items():
            if type_util.is_bytes_like(arg_val):
                bytes_arg = SpecialArg()
                bytes_arg.key = arg_name
                bytes_arg.bytes = to_bytes(arg_val)
                special_args.append(bytes_arg)
            elif type_util.is_dataframe_like(arg_val):
                dataframe_arg = SpecialArg()
                dataframe_arg.key = arg_name
                component_arrow.marshall(dataframe_arg.arrow_dataframe.data, arg_val)
                special_args.append(dataframe_arg)
            else:
                json_args[arg_name] = arg_val

        try:
            serialized_json_args = json.dumps(json_args)
        except Exception as ex:
            raise MarshallComponentException(
                "Could not convert component args to JSON", ex
            )

        def marshall_component(dg, element: Element) -> Union[Any, Type[NoValue]]:
            element.component_instance.component_name = self.name
            element.component_instance.form_id = current_form_id(dg)
            if self.url is not None:
                element.component_instance.url = self.url

            # Normally, a widget's element_hash (which determines
            # its identity across multiple runs of an app) is computed
            # by hashing the entirety of its protobuf. This means that,
            # if any of the arguments to the widget are changed, Streamlit
            # considers it a new widget instance and it loses its previous
            # state.
            #
            # However! If a *component* has a `key` argument, then the
            # component's hash identity is determined by entirely by
            # `component_name + url + key`. This means that, when `key`
            # exists, the component will maintain its identity even when its
            # other arguments change, and the component's iframe won't be
            # remounted on the frontend.
            #
            # So: if `key` is None, we marshall the element's arguments
            # *before* computing its widget_ui_value (which creates its hash).
            # If `key` is not None, we marshall the arguments *after*.

            def marshall_element_args():
                element.component_instance.json_args = serialized_json_args
                element.component_instance.special_args.extend(special_args)

            if key is None:
                marshall_element_args()

            def deserialize_component(ui_value, widget_id=""):
                # ui_value is an object from json, an ArrowTable proto, or a bytearray
                return ui_value

            ctx = get_script_run_ctx()
            component_state = register_widget(
                element_type="component_instance",
                element_proto=element.component_instance,
                user_key=key,
                widget_func_name=self.name,
                deserializer=deserialize_component,
                serializer=lambda x: x,
                ctx=ctx,
            )
            widget_value = component_state.value

            if key is not None:
                marshall_element_args()

            if widget_value is None:
                widget_value = default
            elif isinstance(widget_value, ArrowTableProto):
                widget_value = component_arrow.arrow_proto_to_dataframe(widget_value)

            # widget_value will be either None or whatever the component's most
            # recent setWidgetValue value is. We coerce None -> NoValue,
            # because that's what DeltaGenerator._enqueue expects.
            return widget_value if widget_value is not None else NoValue

        # We currently only support writing to st._main, but this will change
        # when we settle on an improved API in a post-layout world.
        dg = streamlit._main

        element = Element()
        return_value = marshall_component(dg, element)
        result = dg._enqueue(
            "component_instance", element.component_instance, return_value
        )

        return result