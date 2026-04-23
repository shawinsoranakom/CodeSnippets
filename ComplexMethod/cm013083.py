def eval_function(  # type: ignore[override]
        self,
        function: onnxscript.OnnxFunction,
        args: Sequence[AllowedArgType],
        kwargs: Mapping[str, AllowedArgType],
    ) -> _tensors.SymbolicTensor | Sequence[_tensors.SymbolicTensor] | bool | int:
        try:
            # NOTE: signature should be written to function in the registration process
            if hasattr(function, "_pt_onnx_signature"):
                op_signature = function._pt_onnx_signature  # type: ignore[attr-defined]
            else:
                op_signature = _schemas.op_signature_from_function(
                    function,
                    function.function_ir.domain,
                    function.name,
                    since_version=function.opset.version,
                )
                function._pt_onnx_signature = op_signature  # type: ignore[attr-defined]

            named_inputs, named_attrs = _construct_named_inputs_and_attrs(
                op_signature, args, kwargs
            )

            # TODO(after torchlib migration): Remove traceable function handling
            # NOTE: We need to call traceable functions after the _construct_named_inputs_and_attrs
            # call because it will filter out the unexpected kwargs for us.
            if function.traceable:
                # Trace the function call instead of adding the function as a node
                # Turn the ir.Attr objects into Python constants first
                named_attrs = {
                    name: attr.value if isinstance(attr, ir.Attr) else attr
                    for name, attr in named_attrs.items()
                }

                # Use the type binding to resolve the dtypes of the inputs, and
                # convert Python constants to Constant nodes
                type_binding = _resolve_parameter_dtypes(op_signature, named_inputs)
                try:
                    # _process_python_sequences is not here because we want to preserve python list
                    # properties for the function call
                    converted_named_inputs = _process_python_constants(
                        op_signature,
                        named_inputs,
                        type_binding,
                        self.constant_farm,
                        self.opset,
                    )

                except Exception as e:
                    raise _errors.GraphConstructionError(
                        f"Error processing Python constants for operator '{op_signature.domain}::{op_signature.name}'. "
                        f"named_inputs={named_inputs}, named_attrs={named_attrs}, opset={self.opset}, op_signature={op_signature}."
                    ) from e

                return function.function(**converted_named_inputs, **named_attrs)

            outputs = self._call_op(
                op_signature,
                named_inputs,
                named_attrs,
                len(op_signature.outputs),
            )

            self.functions[(function.function_ir.domain, function.name, "")] = function
            if len(outputs) == 1:
                return outputs[0]
            return outputs
        except Exception as e:
            try:
                source_file = inspect.getsourcefile(function.function)
                _, lineno = inspect.getsourcelines(function.function)
            except Exception:
                source_file = lineno = None
            raise _errors.GraphConstructionError(
                f"Error calling function '{function.name}' with args {args} and kwargs {kwargs}."
                + f" The function is defined at '{source_file}:{lineno}'."
                if source_file
                else ""
            ) from e