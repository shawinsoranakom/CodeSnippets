def __call__(
        self,
        frame: DynamoFrameType,
        cache_entry: CacheEntry | None,
        frame_state: dict[str, int | FrameStateSizeEntry],
    ) -> ConvertFrameReturn:
        assert frame_state is not None
        input_codes.add(frame.f_code)

        is_skipfile = trace_rules.check(frame.f_code, frame=frame)
        if sys.version_info >= (3, 13):
            has_started_execution = frame.f_lasti > first_real_inst_idx(frame.f_code)
        else:
            has_started_execution = frame.f_lasti >= first_real_inst_idx(frame.f_code)

        # Check if we should skip due to torch dispatch mode.
        # When inline_torch_dispatch_torch_compile is True (new behavior), we walk
        # the stack to check for active modes. When False (old behavior), we use
        # the global flag that tracks if we're inside any mode.
        if config.inline_torch_dispatch_torch_compile:
            should_skip_for_dispatch_mode = any_torch_dispatch_mode_on_stack()
        else:
            should_skip_for_dispatch_mode = (
                is_in_any_mode_without_ignore_compile_internals()
            )

        if (
            # TODO: the first condition is not covered by any test
            has_started_execution
            or is_skipfile
            or config.disable
            or (
                should_skip_for_dispatch_mode
                and not getattr(self._torchdynamo_orig_backend, "_export", False)
            )
        ):
            if log.isEnabledFor(logging.DEBUG):
                if has_started_execution:
                    skip_reason = "traced frame already"
                elif trace_rules.check(frame.f_code, frame=frame):
                    skip_reason = "in skipfiles"
                elif should_skip_for_dispatch_mode:
                    skip_reason = "non-infra torch dispatch mode present, this is not supported today in torch.compile"
                else:
                    skip_reason = "dynamo tracing is disabled"

                log.debug(
                    "skipping: %s (reason: %s, file: %s)",
                    frame.f_code.co_name,
                    skip_reason,
                    frame.f_code.co_filename,
                )
            return ConvertFrameReturn()

        if (
            frame.f_code.co_filename == "<string>" and frame.f_code.co_name == "__new__"
        ) or (
            frame.f_code.co_filename.endswith("collections/__init__.py")
            and frame.f_code.co_name == "_make"
        ):
            # nametuple constructor/_make
            return ConvertFrameReturn()

        if (
            frame.f_code.co_name == "__init__"
            and frame.f_code.co_argcount > 0
            and frame.f_code.co_varnames
            and is_traceable_wrapper_subclass(
                frame.f_locals.get(frame.f_code.co_varnames[0])
            )
        ):
            # Skip tracing __init__ of traceable wrapper subclasses: self is
            # partially initialized at this point (attributes set by __init__
            # don't exist yet), so faking it would call __tensor_flatten__ and
            # crash. Run eagerly instead, matching @torch._disable_dynamo behavior.
            return ConvertFrameReturn()

        if torch._dynamo.utils.get_optimize_ddp_mode() == "ddp_optimizer":
            ddp_module = DistributedDataParallel._get_active_ddp_module()
            if ddp_module:
                with compile_lock:
                    from torch._dynamo.backends.distributed import DDPOptimizer

                    ddp_optimizer = DDPOptimizer(
                        bucket_bytes_cap=ddp_module.bucket_bytes_cap,
                        backend_compile_fn=self._torchdynamo_orig_backend._torchdynamo_orig_backend,  # type: ignore[attr-defined]
                    )
                    assert hasattr(
                        self._torchdynamo_orig_backend, "_clone_with_backend"
                    ), (
                        "DDPOptimizer only supports callback fns that know how to clone themselves."
                    )
                    hijacked_callback = (
                        self._torchdynamo_orig_backend._clone_with_backend(
                            ddp_optimizer.compile_fn,
                        )
                    )
                    return hijacked_callback(
                        frame, cache_entry, self.hooks, frame_state
                    )

        with compile_lock, _disable_current_modes():
            # skip=1: skip this frame
            result = self._torchdynamo_orig_backend(
                frame, cache_entry, self.hooks, frame_state, skip=1
            )
            return result