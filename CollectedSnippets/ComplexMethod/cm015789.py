def _capture_graph_and_evaluate_torch_script_evaluator(
        function: Callable, args, kwargs
    ) -> tuple[Any, onnx.ModelProto]:
        """Captures the graph of a function and evaluates it using TorchScriptEvaluator."""

        # Initialize the ONNX graph
        graph = ir.Graph(
            (),
            (),
            nodes=(),
            opset_imports={"": opset_version, "pkg.torch.onnx": 1},
            name="main_graph",
        )
        opset = onnxscript.values.Opset("", opset_version)
        tracer = _building.OpRecorder(opset, {})
        ort_inputs = {}
        onnxscript_args: list[Any] = []
        onnxscript_kwargs = {}
        for i, arg in enumerate(args):
            if isinstance(arg, np.ndarray):
                input_name = f"input_{i}"
                input = _tensors.SymbolicTensor(
                    opset=opset,
                    name=input_name,
                    shape=ir.Shape(arg.shape),
                    type=ir.TensorType(
                        _TORCH_DTYPE_TO_ONNX_TYPE[torch.tensor(arg).dtype]
                    ),
                )
                graph.inputs.append(input)
                onnxscript_args.append(input)
                ort_inputs[input_name] = arg
            elif isinstance(arg, (list, tuple)):
                # str is also a sequence but we do not want to treat it as a tensor
                sequence_input = []
                for j, subarg in enumerate(arg):
                    if isinstance(subarg, np.ndarray):
                        input_name = f"input_{i}_{j}"
                        tensor = torch.tensor(subarg)
                        input = _tensors.SymbolicTensor(
                            opset=opset,
                            name=input_name,
                            shape=ir.Shape(tensor.shape),
                            type=ir.TensorType(_TORCH_DTYPE_TO_ONNX_TYPE[tensor.dtype]),
                        )
                        graph.inputs.append(input)
                        sequence_input.append(input)
                        ort_inputs[input_name] = subarg
                    else:
                        # Include non-numpy inputs as-is
                        # For example, it could be a None value that we want to keep
                        sequence_input.append(subarg)
                onnxscript_args.append(sequence_input)
            else:
                onnxscript_args.append(arg)
        for key, value in kwargs.items():
            if isinstance(value, np.ndarray):
                input = _tensors.SymbolicTensor(
                    opset=opset,
                    name=key,
                    shape=ir.Shape(torch.tensor(value).shape),
                    type=ir.TensorType(
                        _TORCH_DTYPE_TO_ONNX_TYPE[torch.tensor(value).dtype]
                    ),
                )
                graph.inputs.append(input)
                ort_inputs[key] = value
                onnxscript_kwargs[key] = input
            else:
                onnxscript_kwargs[key] = value

        with onnxscript.evaluator.default_as(tracer):
            symbolic_outputs = function(*onnxscript_args, **onnxscript_kwargs)
        if not isinstance(symbolic_outputs, Sequence):
            symbolic_outputs = (symbolic_outputs,)

        # We need to set the size of the output tensors for the ONNX model to be valid
        for output, symbolic_output in zip(outputs, symbolic_outputs):
            if isinstance(output, Sequence):
                # Output is a sequence
                elem_dtype = _TORCH_DTYPE_TO_ONNX_TYPE[output[0].dtype]
                symbolic_output.type = ir.SequenceType(ir.TensorType(elem_dtype))
                continue
            output = (
                output
                if isinstance(output, torch.Tensor)
                else torch.tensor(output, device="cpu")
            )
            symbolic_output.shape = ir.Shape(output.shape)
            symbolic_output.dtype = _TORCH_DTYPE_TO_ONNX_TYPE[output.dtype]

        graph.outputs.extend(symbolic_outputs)
        graph.extend(tracer.nodes)
        onnx_model = ir.Model(graph, ir_version=10, producer_name="torch_test")
        for identifier, onnxscript_function in tracer.functions.items():
            if identifier in onnx_model.functions:
                continue
            if isinstance(onnxscript_function, ir.Function):
                ir_function = onnxscript_function
            else:
                # TODO: Get IR function directly when onnxscript is updated
                proto = onnxscript_function.to_function_proto()
                ir_function = ir.serde.deserialize_function(proto)
            onnx_model.functions[identifier] = ir_function
        _ir_passes.add_opset_imports(onnx_model)
        # Make sure the model is valid
        model_proto = ir.to_proto(onnx_model)
        try:
            onnx.checker.check_model(model_proto, full_check=True)
        except (onnx.checker.ValidationError, onnx.shape_inference.InferenceError) as e:
            raise AssertionError(f"ONNX model is invalid. Model:\n{onnx_model}") from e
        model_proto = onnx.shape_inference.infer_shapes(model_proto, data_prop=True)
        try:
            if (
                os.environ.get("CATCH_ORT_SEGFAULT") == "1"
                or os.environ.get("CREATE_REPRODUCTION_REPORT") == "1"
            ):
                # Use an individual process to run ONNX Runtime to catch segfaults
                return _safe_ort_session_run(
                    model_proto.SerializeToString(), ort_inputs
                ), model_proto

            return _ort_session_run(
                model_proto.SerializeToString(), ort_inputs
            ), model_proto
        except (
            # pylint: disable=c-extension-no-member
            onnxruntime.capi.onnxruntime_pybind11_state.Fail,
            onnxruntime.capi.onnxruntime_pybind11_state.RuntimeException,
            onnxruntime.capi.onnxruntime_pybind11_state.InvalidArgument,
            onnxruntime.capi.onnxruntime_pybind11_state.InvalidGraph,
            onnxruntime.capi.onnxruntime_pybind11_state.NotImplemented,
            # pylint: enable=c-extension-no-member
        ) as e:
            if os.environ.get("CREATE_REPRODUCTION_REPORT") == "1":
                error_reproduction.create_reproduction_report(
                    test_name,
                    model_proto,
                    ort_inputs,
                    e,
                    "test/onnx/torchlib/test_ops.py",
                )
            raise RuntimeError(
                "ONNX Runtime failed to evaluate:\n"
                + _format_model_and_input_information(model_proto, ort_inputs)
            ) from e
        except OrtAbortedError as e:
            if os.environ.get("CREATE_REPRODUCTION_REPORT") == "1":
                # Save the model and inputs to a file for reproduction
                error_reproduction.create_reproduction_report(
                    test_name,
                    model_proto,
                    ort_inputs,
                    e,
                    "test/onnx/torchlib/test_ops.py",
                )
            raise OrtAbortedError(
                "ONNX Runtime aborted:\n"
                + _format_model_and_input_information(model_proto, ort_inputs)
            ) from e
        except Exception as e:
            if os.environ.get("CREATE_REPRODUCTION_REPORT") == "1":
                error_reproduction.create_reproduction_report(
                    test_name,
                    model_proto,
                    ort_inputs,
                    e,
                    "test/onnx/torchlib/test_ops.py",
                )
            raise