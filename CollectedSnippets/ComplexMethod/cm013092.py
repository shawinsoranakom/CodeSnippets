def check_discrepancies(
        self,
        onnx_program: torch.onnx.ONNXProgram,
        atol: float = 1e-4,
        rtol: float = 0.1,
        progress_bar: bool = False,
        initializer: Callable[
            [str | bytes], ort.InferenceSession
        ] = _onnx_program._ort_session_initializer,
        skip_none: bool = True,
    ) -> list[dict[str, str | int | float | bool]]:
        """Computes the discrepancies between the saved inputs and outputs
        with the saved onnx model.

        Args:
            onnx_program: Exported Model to verify.
            atol: Absolute tolerance, recommended values, 1e-4 for float, 1e-2 for float16.
            rtol: Relative tolerance.
            progress_bar: Shows a progress bar (requires `tqdm`).
            initializer: The function called to initialize the ONNX Runtime inference
                session with the specified model. By default, it uses the
                `_ort_session_initializer` function.
            skip_none: Does not check discrepancies when an output is None.

        Returns:
            A list of dictionaries, ready to be consumed by a dataframe.

        The function catches exceptions, it shows the error in the returned
        summary.
        """
        # For big models, we should consider taking a filename to avoid the users
        # creating the model proto twice.
        self._check_captured()
        assert self.info is not None  # noqa: S101

        onnx_program.initialize_inference_session(initializer)

        input_names = [i.name for i in onnx_program.model.graph.inputs]
        io_sets = list(
            zip(self.info.inputs, self.info.flat_outputs, self.info.latencies)
        )
        if progress_bar:
            from tqdm import tqdm

            loop = tqdm(io_sets)
        else:
            loop = io_sets
        data: list[dict[str, Any]] = []
        for inputs, outputs, latency in loop:
            assert inputs.aligned_flat_list is not None  # noqa: S101
            if len(input_names) != len(inputs.aligned_flat_list):
                raise RuntimeError(
                    f"There are ({len(inputs.aligned_flat_list)}) "
                    f"tensors but the model expects {len(input_names)}."
                )
            n_none = sum(t is None for t in inputs.aligned_flat_list)
            n_empty = sum(t is None or t.numel() == 0 for t in inputs.aligned_flat_list)

            feeds = dict(zip(input_names, self.info.infer_arguments(inputs, flat=True)))

            begin = time.perf_counter()
            try:
                ort_outputs = onnx_program(**feeds)
                error = None
            except Exception as e:
                error = str(e)
                ort_outputs = None

            duration = time.perf_counter() - begin
            if error:
                diff: dict[str, str | int | float | bool] = dict(
                    error=error, SUCCESS=False
                )
            elif ort_outputs is None or len(outputs) != len(ort_outputs):
                diff = dict(SUCCESS=False, error="not the same number of outputs")
            else:
                success = True
                err_abs = 0.0
                err_rel = 0.0
                error = ""
                for torch_tensor, ort_tensor in zip(outputs, ort_outputs):
                    if torch_tensor is None or ort_tensor is None:
                        if type(torch_tensor) is not type(ort_tensor) and not skip_none:
                            success = False
                            error = "missing output"
                            break
                        continue
                    if torch_tensor.shape != ort_tensor.shape:
                        success = False
                        error = "not the same shape"
                        break
                    if torch_tensor.dtype != ort_tensor.dtype:
                        success = False
                        error = "not the same type"
                        break
                    err = (torch_tensor - ort_tensor).abs().max().item()
                    err_abs = max(err_abs, err)
                    if err_abs > atol:
                        success = False
                    err = (
                        (
                            (torch_tensor - ort_tensor).abs()
                            / (torch_tensor.abs() + rtol)
                        )
                        .max()
                        .item()
                    )
                    err_rel = max(err_rel, err)
                    if err_rel > rtol:
                        success = False
                diff = dict(SUCCESS=success, abs=err_abs, rel=err_rel)
            diff.update(
                dict(
                    index=len(data),
                    duration_torch=latency,
                    ort_duration=duration,
                    n_inputs=len(input_names),
                    n_none=n_none,
                    n_empty=n_empty,
                )
            )
            data.append(diff)
        onnx_program.release()
        return data