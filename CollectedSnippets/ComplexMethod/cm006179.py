def _add_component(clazz: type, inputs: dict | None = None) -> str:
        raw_inputs = {}
        if inputs:
            for key, value in inputs.items():
                if not isinstance(value, ComponentInputHandle):
                    raw_inputs[key] = value
                if isinstance(value, Component):
                    msg = "Component inputs must be wrapped in ComponentInputHandle"
                    raise TypeError(msg)
        component = clazz(**raw_inputs, _user_id=user_id)
        component_id = graph.add_component(component)
        if inputs:
            for input_name, handle in inputs.items():
                if isinstance(handle, ComponentInputHandle):
                    handle_component_id = _add_component(handle.clazz, handle.inputs)
                    graph.add_component_edge(handle_component_id, (handle.output_name, input_name), component_id)
        return component_id