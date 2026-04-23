def draft_export(
    mod: torch.nn.Module,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any] | None = None,
    *,
    dynamic_shapes: dict[str, Any] | tuple[Any] | list[Any] | None = None,
    preserve_module_call_signature: tuple[str, ...] = (),
    strict: bool = False,
    pre_dispatch: bool = True,
    prefer_deferred_runtime_asserts_over_guards: bool = False,
) -> ExportedProgram:
    start_time = time.time()
    kwargs = kwargs or {}
    dynamic_shapes = dynamic_shapes or {}

    constraint_violation_msg = None
    capture_structured_log = CaptureStructuredTrace()

    with (
        torch._functorch.config.patch(
            fake_tensor_propagate_real_tensors=True,
            generate_fake_kernels_from_real_mismatches=True,
        ),
        capture_structured_log,
    ):
        try:
            new_shapes = None
            ep = _export(
                mod,
                args,
                kwargs,
                dynamic_shapes=dynamic_shapes,
                strict=strict,
                pre_dispatch=pre_dispatch,
                preserve_module_call_signature=preserve_module_call_signature,
                prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
            )
        except Exception as exc:
            if (
                isinstance(exc, UserError)
                and exc.error_type == UserErrorType.CONSTRAINT_VIOLATION
            ):
                constraint_violation_msg = exc.msg

                def convert_dim_to_auto(dim: Any) -> Any:
                    if isinstance(dim, Dim):
                        return Dim.AUTO(min=dim.min, max=dim.max)
                    elif isinstance(dim, _DimHint) and dim.type == _DimHintType.DYNAMIC:
                        return Dim.AUTO(min=dim.min, max=dim.max)
                    return dim

                new_shapes = pytree.tree_map(convert_dim_to_auto, dynamic_shapes)
                ep = _export(
                    mod,
                    args,
                    kwargs,
                    dynamic_shapes=new_shapes,
                    strict=strict,
                    pre_dispatch=pre_dispatch,
                    preserve_module_call_signature=preserve_module_call_signature,
                    prefer_deferred_runtime_asserts_over_guards=prefer_deferred_runtime_asserts_over_guards,
                )
            else:
                log_draft_export_usage(
                    error=True,
                    export_time=time.time() - start_time,
                    strict=strict,
                    message=str(exc),
                    type=f"{type(exc).__name__}.{type(exc).__qualname__}",
                )
                raise exc

        torch._logging.dtrace_structured("exported_program", payload_fn=lambda: str(ep))

        str_to_filename: dict[int, str] = {}
        failures: list[FailureReport] = []
        incorrect_custom_ops: set[str] = set()
        expressions_created: dict[int, dict[str, Any]] = {}

        for log_name, log_contents in capture_structured_log.log_record.logs:
            failure_type = None

            if log_name == "str":
                str_to_filename[log_contents[1]] = log_contents[0]  # type: ignore[index]
                continue

            elif log_name == "propagate_real_tensors_provenance":
                log_contents["occurrences"] = (
                    capture_structured_log.log_record.get_log_count(
                        (log_name, log_contents)
                    )
                )

                failure_type = FailureType.DATA_DEPENDENT_ERROR

            elif log_name == "guard_added":
                if new_shapes is None:
                    continue

                failure_type = FailureType.GUARD_ADDED
                log_contents["new_dynamic_shapes"] = new_shapes
            elif log_name == "missing_fake_kernel":
                failure_type = FailureType.MISSING_FAKE_KERNEL
                incorrect_custom_ops.add(log_contents["op"])

            elif log_name == "mismatched_fake_kernel":
                failure_type = FailureType.MISMATCHED_FAKE_KERNEL
                incorrect_custom_ops.add(log_contents["op"])

            else:
                continue

            if failure_type is None:
                raise AssertionError("failure_type cannot be None at this point")
            failures.append(
                FailureReport(
                    failure_type,
                    log_contents,
                )
            )

        for k, v in capture_structured_log.expression_created_logs.items():
            if v.visited:
                expressions_created[k] = v.record

        op_profiles = get_op_profiles(ep.graph_module, incorrect_custom_ops)
        report = DraftExportReport(
            failures, str_to_filename, expressions_created, op_profiles
        )

        # Add asserts around custom ops
        insert_custom_op_guards(ep.graph_module, incorrect_custom_ops)

    ep._report = report
    if not report.successful():
        log_filename = capture_structured_log.stream.name

        warning_msg = f"""
###################################################################################################
WARNING: {len(report.failures)} issue(s) found during export, and it was not able to soundly produce a graph.
To view the report of failures in an html page, please run the command:
    `tlparse {log_filename} --export`
Or, you can view the errors in python by inspecting `print(ep._report)`.
"""

        if len(report.op_profiles) > 0:
            warning_msg += f"""
While tracing we found {len(report.op_profiles)} operator(s) which do not have a fake kernel registered.
If you intend to retrace the exported graph or run it with fake tensors, please run it under the
following context manager, which will register a fake kernel for those operators.
```
with torch._library.fake_profile.unsafe_generate_fake_kernels(ep._report.op_profiles):
    # run with fake tensors
```
"""

        warning_msg += """#################################################################################################"""

        log.warning(warning_msg)

    else:
        log.info(
            """
##############################################################################################
Congratuations: No issues are found during export, and it was able to soundly produce a graph.
You can now change back to torch.export.export()
##############################################################################################
    """
        )

    log_draft_export_usage(
        error=False,
        export_time=time.time() - start_time,
        strict=strict,
        constraint_violations=constraint_violation_msg,
        report=ep._report,
        **get_ep_stats(ep),
    )
    return ep