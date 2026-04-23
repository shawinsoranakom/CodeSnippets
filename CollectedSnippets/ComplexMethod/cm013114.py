def export(
    model: torch.nn.Module
    | torch.export.ExportedProgram
    | torch.fx.GraphModule
    | torch.jit.ScriptModule
    | torch.jit.ScriptFunction,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    *,
    registry: _registration.ONNXRegistry | None = None,
    dynamic_shapes: dict[str, Any] | tuple[Any, ...] | list[Any] | None = None,
    input_names: Sequence[str] | None = None,
    output_names: Sequence[str] | None = None,
    report: bool = False,
    verify: bool = False,
    profile: bool = False,
    dump_exported_program: bool = False,
    artifacts_dir: str | os.PathLike = ".",
    verbose: bool | None = None,
    optimize: bool = True,
    opset_version: int | None = None,
) -> _onnx_program.ONNXProgram:
    """Export a PyTorch model to ONNXProgram.

    Args:
        model: The model to export. This can be a PyTorch nn.Module or an ExportedProgram.
        args: The arguments to pass to the model.
        kwargs: The keyword arguments to pass to the model.
        registry: The registry of all ONNX decompositions.
        dynamic_shapes: Dynamic shapes in the graph.
        input_names: If provided, rename the inputs.
        output_names: If provided, rename the outputs.
        report: Whether to generate an error report if the export fails.
        verify: Whether to verify the ONNX model after exporting.
        profile: Whether to profile the export process. When report is True,
            the profile result will be saved in the report. Otherwise, the profile
            result will be printed.
        dump_exported_program: Whether to save the exported program to a file.
        artifacts_dir: The directory to save the exported program and error reports.
        verbose: Whether to print verbose messages. If None (default), some messages will be printed.
        optimize: Whether to optimize the exported ONNX graph.
        opset_version: The ONNX opset version to use. If None, use the default opset version
            from the registry.

    Returns:
        The ONNXProgram with the exported IR graph.

    Raises:
        TorchExportError: If the export process fails with torch.export.
        ConversionError: If the ExportedProgram to ONNX translation fails.
    """
    # Set up the error reporting facilities
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    profiler = _maybe_start_profiler(profile)

    # Create the artifacts directory if it does not exist
    artifacts_dir = pathlib.Path(artifacts_dir)
    if report or profile or dump_exported_program:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

    verbose_print = _verbose_printer(verbose)
    export_status = _reporting.ExportStatus()
    failed_results: list[_capture_strategies.Result] = []

    program: torch.export.ExportedProgram | None = None
    capture_strategy: str | None = None
    # Step 1: Export the model with torch.export.export if the model is not already an ExportedProgram
    if isinstance(model, torch.export.ExportedProgram):
        # We know the model is already exported program, so the args, kwargs, and dynamic_shapes
        # are not used.
        program = model
        # torch.export.export has strict default to False
        export_status.torch_export_non_strict = True
    else:
        # Convert an nn.Module to an ExportedProgram
        # Try everything 🐰 (all paths for getting an ExportedProgram)
        result: _capture_strategies.Result | None = None
        for strategy_class in _capture_strategies.CAPTURE_STRATEGIES:
            strategy = strategy_class(  # type: ignore[abstract]
                verbose=verbose is not False,  # Treat None as verbose
                dump=dump_exported_program,
                artifacts_dir=artifacts_dir,
                timestamp=timestamp,
            )
            result = strategy(model, args, kwargs, dynamic_shapes=dynamic_shapes)

            # Record the status
            if strategy_class is _capture_strategies.TorchExportNonStrictStrategy:
                export_status.torch_export_non_strict = result.success
            elif strategy_class is _capture_strategies.TorchExportStrictStrategy:
                export_status.torch_export_strict = result.success
            elif strategy_class is _capture_strategies.TorchExportDraftExportStrategy:
                export_status.torch_export_draft_export = result.success

            if result.exception is not None:
                failed_results.append(result)
            if result.success:
                if result.exported_program is None:
                    raise AssertionError("exported_program must be non-None on success")
                program = result.exported_program
                break

        if result is None:
            raise AssertionError("result must be non-None")
        capture_strategy = result.strategy
        if result.exported_program is None:
            # If all strategies fail, produce an error report and raise the first error
            profile_result = _maybe_stop_profiler_and_get_result(profiler)

            if report:
                report_path = artifacts_dir / _reporting.construct_report_file_name(
                    timestamp, export_status
                )

                try:
                    _reporting.create_torch_export_error_report(
                        report_path,
                        _format_exceptions_for_all_strategies(failed_results),
                        export_status=export_status,
                        profile_result=profile_result,
                    )
                except Exception as e_report:
                    verbose_print(
                        f"Failed to save error report due to an error: {e_report}"
                    )
            else:
                report_path = None

            first_error = failed_results[0].exception
            if first_error is None:
                raise AssertionError("first_error must be non-None")

            # NOTE: We only throw the torch.export (first) exception because we want to
            # focus on the torch.export.export error. Errors from other strategies like
            # torch.jit.trace is due to the fallback and can be confusing to users.
            # We save all errors in the error report.
            raise _errors.TorchExportError(
                _STEP_ONE_ERROR_MESSAGE
                + (
                    f"\nError report has been saved to '{report_path}'."
                    if report
                    else ""
                )
                + _summarize_exception_stack(first_error)
            ) from first_error

    if program is None:
        raise AssertionError("program must be non-None")

    if dump_exported_program:
        verbose_print("Dumping ExportedProgram because `dump_exported_program=True`...")
        program_path = artifacts_dir / f"onnx_export_{timestamp}.pt2"
        try:
            torch.export.save(program, program_path)
        except Exception as e:
            verbose_print(f"Failed to save ExportedProgram due to an error: {e}")
        else:
            verbose_print(f"ExportedProgram has been saved to '{program_path}'.")

    # Step 2: Decompose the exported program and insert type promotion nodes
    verbose_print("Run decompositions...")

    try:
        # Build the ONNX function registry
        if registry is None:
            registry = _registration.ONNXRegistry.from_torchlib()

        # Process the exported program to run decompositions and type promotions etc.
        decomposed_program = _prepare_exported_program_for_export(
            program, registry=registry
        )
    except Exception as e:
        export_status.decomposition = False
        verbose_print("Run decompositions... ❌")
        profile_result = _maybe_stop_profiler_and_get_result(profiler)

        if report:
            report_path = artifacts_dir / _reporting.construct_report_file_name(
                timestamp, export_status
            )

            # Run the analysis to get the error report
            try:
                _reporting.create_onnx_export_report(
                    report_path,
                    f"{_format_exceptions_for_all_strategies(failed_results)}\n\n{_format_exception(e)}",
                    program,
                    export_status=export_status,
                    profile_result=profile_result,
                    registry=registry,
                )
            except Exception:
                logger.exception("Failed to save report due to an error.")
        else:
            report_path = None

        raise _errors.ConversionError(
            _STEP_TWO_ERROR_MESSAGE
            + (f"\nError report has been saved to '{report_path}'." if report else "")
            + _summarize_exception_stack(e)
        ) from e
    else:
        export_status.decomposition = True
        verbose_print("Run decompositions... ✅")

    # Step 3: Translate the decomposed program to ONNX and produce ONNXProgram
    verbose_print("Translate the graph into ONNX...")
    if report or profile:
        pre_decomp_unique_ops, post_decomp_unique_ops = _analysis.compare_ops(
            program, decomposed_program
        )
    else:
        pre_decomp_unique_ops = None
        post_decomp_unique_ops = None

    try:
        # Convert the exported program to an ONNX model
        onnx_program = _exported_program_to_onnx_program(
            decomposed_program, registry=registry
        )
        # Record the strategy used for getting the exported program for unit test assertions
        onnx_program._capture_strategy = capture_strategy

        export_status.onnx_translation = True
        verbose_print("Translate the graph into ONNX... ✅")
    except Exception as e:
        export_status.onnx_translation = False
        verbose_print("Translate the graph into ONNX... ❌")
        profile_result = _maybe_stop_profiler_and_get_result(profiler)

        if report:
            report_path = artifacts_dir / _reporting.construct_report_file_name(
                timestamp, export_status
            )

            try:
                if pre_decomp_unique_ops is None:
                    raise AssertionError("pre_decomp_unique_ops must be non-None")
                if post_decomp_unique_ops is None:
                    raise AssertionError("post_decomp_unique_ops must be non-None")

                # Run the analysis to get the error report
                _reporting.create_onnx_export_report(
                    report_path,
                    f"{_format_exceptions_for_all_strategies(failed_results)}\n\n{_format_exception(e)}",
                    decomposed_program,
                    decomp_comparison=_reporting.format_decomp_comparison(
                        pre_decomp_unique_ops, post_decomp_unique_ops
                    ),
                    export_status=export_status,
                    profile_result=profile_result,
                    registry=registry,
                )
                verbose_print(f"Export report has been saved to '{report_path}'.")
            except Exception:
                logger.exception("Failed to save report due to an error.")
        else:
            report_path = None

        raise _errors.ConversionError(
            _STEP_THREE_ERROR_MESSAGE
            + (f"\nError report has been saved to '{report_path}'." if report else "")
            + _summarize_exception_stack(e)
        ) from e

    profile_result = _maybe_stop_profiler_and_get_result(profiler)

    if onnx_program.exported_program is None:
        raise AssertionError("exported_program must be non-None")

    # Converter opset version and optimize
    if opset_version is not None:
        onnx_program.model = onnxscript_apis.convert_version(
            onnx_program.model, opset_version
        )

    if optimize:
        verbose_print("Optimize the ONNX graph...")
        onnx_program.optimize()
        verbose_print("Optimize the ONNX graph... ✅")

    # Run the ONNX passes
    if input_names:
        _ir_passes.rename_inputs(onnx_program.model, input_names)
    if output_names:
        _ir_passes.rename_outputs(onnx_program.model, output_names)

    if not verify:
        # Return if verification is not requested
        if report:
            try:
                if pre_decomp_unique_ops is None:
                    raise AssertionError("pre_decomp_unique_ops must be non-None")
                if post_decomp_unique_ops is None:
                    raise AssertionError("post_decomp_unique_ops must be non-None")
                report_path = artifacts_dir / _reporting.construct_report_file_name(
                    timestamp, export_status
                )
                _reporting.create_onnx_export_report(
                    report_path,
                    "No errors"
                    if not failed_results
                    else _format_exceptions_for_all_strategies(failed_results),
                    onnx_program.exported_program,
                    decomp_comparison=_reporting.format_decomp_comparison(
                        pre_decomp_unique_ops, post_decomp_unique_ops
                    ),
                    export_status=export_status,
                    profile_result=profile_result,
                    model=onnx_program.model,
                    registry=registry,
                )
                verbose_print(f"Export report has been saved to '{report_path}'.")
            except Exception:
                logger.exception("Failed to save report due to an error.")
        elif profile and profile_result is not None:
            verbose_print("Profile result:")
            verbose_print(profile_result)
        return onnx_program

    # Step 4: (verify=True) Check the ONNX model with ONNX checker
    try:
        verbose_print("Check the ONNX model...")
        onnxscript_apis.check_model(onnx_program.model)
        export_status.onnx_checker = True
        verbose_print("Check the ONNX model... ✅")
    except Exception as e:
        export_status.onnx_checker = False
        verbose_print("Check the ONNX model... ❌")
        if report:
            try:
                if pre_decomp_unique_ops is None:
                    raise AssertionError("pre_decomp_unique_ops must be non-None")
                if post_decomp_unique_ops is None:
                    raise AssertionError("post_decomp_unique_ops must be non-None")
                report_path = artifacts_dir / _reporting.construct_report_file_name(
                    timestamp, export_status
                )
                _reporting.create_onnx_export_report(
                    report_path,
                    f"{_format_exceptions_for_all_strategies(failed_results)}\n\n{_format_exception(e)}",
                    onnx_program.exported_program,
                    decomp_comparison=_reporting.format_decomp_comparison(
                        pre_decomp_unique_ops, post_decomp_unique_ops
                    ),
                    export_status=export_status,
                    profile_result=profile_result,
                    model=onnx_program.model,
                    registry=registry,
                )
                verbose_print(f"Export report has been saved to '{report_path}'.")
            except Exception:
                logger.exception("Failed to save report due to an error.")
        logger.warning(
            "Conversion successful but the ONNX model fails ONNX checker. "  # noqa: G004
            "Please create an issue "
            f"in the PyTorch GitHub repository against the {_BLUE}*onnx*{_END} component and "
            "attach the full error stack as well as reproduction scripts. ",
            exc_info=e,
        )
        return onnx_program

    # Step 5: (verify=True) Execute the model with ONNX Runtime
    try:
        verbose_print("Execute the model with ONNX Runtime...")
        verification_results = _verification.verify_onnx_program(onnx_program)
        verbose_print("Execute the model with ONNX Runtime... ✅")
        export_status.onnx_runtime = True
        onnx_runtime_error_message = None
    except Exception as e:
        verbose_print("Execute the model with ONNX Runtime... ❌")
        export_status.onnx_runtime = False
        onnx_runtime_error_message = _format_exception(e)
        verification_message = None

    else:
        # Step 6: (verify=True) Validate the output values
        verbose_print("Verify output accuracy...")
        export_status.output_accuracy = True
        for verification_result in verification_results:
            # TODO(justinchuby): The threshold is arbitrary right now
            if verification_result.max_abs_diff >= 5e-3:
                logger.warning(
                    "Output '%s' has a large absolute difference of %f. ",
                    verification_result.name,
                    verification_result.max_abs_diff,
                )
                export_status.output_accuracy = False
            if verification_result.max_rel_diff >= 1e-1:
                logger.warning(
                    "Output '%s' has a large relative difference of %f. ",
                    verification_result.name,
                    verification_result.max_rel_diff,
                )
                export_status.output_accuracy = False
        if export_status.output_accuracy:
            verbose_print("Verify output accuracy... ✅")
        else:
            verbose_print("Verify output accuracy... ❌")
        verification_message = _reporting.format_verification_infos(
            verification_results
        )

    if report:
        try:
            if pre_decomp_unique_ops is None:
                raise AssertionError("pre_decomp_unique_ops must be non-None")
            if post_decomp_unique_ops is None:
                raise AssertionError("post_decomp_unique_ops must be non-None")

            traceback_lines = []
            if failed_results:
                traceback_lines.append(
                    _format_exceptions_for_all_strategies(failed_results)
                )
            if onnx_runtime_error_message:
                traceback_lines.append("# ⚠️ ONNX Runtime error -----------------------")
                traceback_lines.append(onnx_runtime_error_message)
            if not traceback_lines:
                traceback_lines.append("No errors")

            report_path = artifacts_dir / _reporting.construct_report_file_name(
                timestamp, export_status
            )
            _reporting.create_onnx_export_report(
                report_path,
                "\n\n".join(traceback_lines),
                onnx_program.exported_program,
                profile_result=profile_result,
                export_status=export_status,
                decomp_comparison=_reporting.format_decomp_comparison(
                    pre_decomp_unique_ops, post_decomp_unique_ops
                ),
                model=onnx_program.model,
                registry=registry,
                verification_result=verification_message,
            )
            verbose_print(f"Export report has been saved to '{report_path}'.")
        except Exception:
            logger.exception("Failed to save report due to an error.")

    # Release the inference session created during verification
    onnx_program.release()
    return onnx_program