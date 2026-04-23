def set_input_value(self, name: str, value: Any) -> None:
        if name in self._inputs:
            input_value = self._inputs[name].value
            if isinstance(input_value, Component):
                methods = ", ".join([f"'{output.method}'" for output in input_value.outputs])
                msg = self.build_input_error_message(
                    name,
                    f"You set {input_value.display_name} as value. You should pass one of the following: {methods}",
                )
                raise ValueError(msg)
            if callable(input_value) and hasattr(input_value, "__self__"):
                msg = self.build_input_error_message(
                    name, f"Input is connected to {input_value.__self__.display_name}.{input_value.__name__}"
                )
                raise ValueError(msg)
            try:
                self._inputs[name].value = value
            except Exception as e:
                msg = f"Error setting input value for {name}: {e}"
                raise ValueError(msg) from e
            if hasattr(self._inputs[name], "load_from_db"):
                self._inputs[name].load_from_db = False
        else:
            msg = self.build_component_error_message(f"Input {name} not found")
            raise ValueError(msg)