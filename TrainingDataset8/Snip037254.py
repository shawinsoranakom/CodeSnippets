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