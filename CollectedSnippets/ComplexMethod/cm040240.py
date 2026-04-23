def _standardize_inputs(self, inputs):
        raise_exception = False
        if (
            isinstance(self._inputs_struct, list)
            and len(self._inputs_struct) == 1
            and ops.is_tensor(inputs)
        ):
            inputs = [inputs]
        elif isinstance(inputs, dict) and not isinstance(
            self._inputs_struct, dict
        ):
            # This is to avoid warning
            # when we have reconcilable dict/list structs
            if hasattr(self._inputs_struct, "__len__") and all(
                isinstance(i, backend.KerasTensor) for i in self._inputs_struct
            ):
                expected_keys = set(i.name for i in self._inputs_struct)
                keys = set(inputs.keys())
                if expected_keys.issubset(keys):
                    inputs = [inputs[i.name] for i in self._inputs_struct]
                else:
                    raise_exception = True
            elif isinstance(self._inputs_struct, backend.KerasTensor):
                if self._inputs_struct.name in inputs:
                    inputs = [inputs[self._inputs_struct.name]]
                else:
                    raise_exception = True
            else:
                raise_exception = True
        if (
            isinstance(self._inputs_struct, dict)
            and not isinstance(inputs, dict)
            and list(self._inputs_struct.keys())
            != sorted(self._inputs_struct.keys())
        ):
            raise_exception = True
        self._maybe_warn_inputs_struct_mismatch(
            inputs, raise_exception=raise_exception
        )

        flat_inputs = tree.flatten(inputs)
        flat_inputs = self._convert_inputs_to_tensors(flat_inputs)
        return self._adjust_input_rank(flat_inputs)