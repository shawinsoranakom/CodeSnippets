def __call__(
        self,
        frame: DynamoFrameType,
        cache_entry: CacheEntry | None,
        hooks: Hooks,
        frame_state: dict[str, int | FrameStateSizeEntry],
        skip: int = 0,
    ) -> ConvertFrameReturn:
        input_codes.add(frame.f_code)
        counters["frames"]["total"] += 1
        try:
            result = self._inner_convert(
                frame, cache_entry, hooks, frame_state, skip=skip + 1
            )
            counters["frames"]["ok"] += 1
            return result
        except Exception as e:
            # Do not allow errors to be suppressed if we're tracing a resume function prologue
            if isinstance(e, ResumePrologueTracingError):
                raise

            error_on_graph_break = (
                self._inner_convert._box.error_on_graph_break is not None
            )
            assert error_on_graph_break is not None
            if self._inner_convert._box.error_on_graph_break:
                # NOTE we _might_ have to wrap the current in a custom exception
                # in order to correctly bubble up to the top-level compile wrapper in
                # eval_frame.py. But re-raising seems to work for now because exceptions from tracing
                # a nested call that results in a top-level frame compile will be handled by the caller
                # as an observed exception - we don't expect that exception to be suppressed.
                raise

            # These two exception types are "soft" failure, in the sense that
            # we know this is due to something we didn't implement all the
            # way, scare the user less about it.  That being said, if you
            # are trying to understand why a graph break happened, it's still
            # important to have this information, so offer it.
            #
            # NB: NotImplementedError used to be on this list, but actually
            # it is impossible for it to reach here, as it is converted into
            # InternalTorchDynamoError.  This behavior seemed reasonable
            # to me (ezyang, Aug 2023) so I kept it, but maybe at some point
            # someone wanted these to also get suppressed.  If so, you'll
            # need to make these exceptions not get wrapped

            # We intentionally don't want to suppress error here.
            if isinstance(e, UncapturedHigherOrderOpError):
                raise

            soft_fail = isinstance(e, (Unsupported, UserError))
            code = frame.f_code
            # Log soft failure that was not already logged by symbolic_convert.
            # This happens e.g. for graph breaks that are raised in convert_frame.py
            # TODO(williamwen42) Unsupported exn's from tracing are handled and logged by symbolic_convert.py
            # Unsupported exn's caught here should be from convert_frame.py - figure out a better way
            # to log these.
            if (
                soft_fail
                and not getattr(e, "logged", False)
                and graph_break_log.isEnabledFor(logging.DEBUG)
            ):
                # Log this message in the graph break. Also use the string
                # "skip: " to tell that the whole frame is falling back to
                # eager.
                if hasattr(e, "compile_id") and hasattr(e, "real_stack"):
                    with compile_context(CompileContext(e.compile_id)):  # type: ignore[attr-defined]
                        user_stack = e.real_stack
                        user_stack_formatted = "".join(
                            traceback.format_list(user_stack)
                        )
                        frame_info = exc.format_frame_info(code)
                        user_stack_trace = (
                            "Graph break: torch.compile cannot properly resume from this graph break, which results in a skip.\n"
                            f"torch.compile will skip tracing the frame {frame_info} and fall back to eager.\n"
                            "The graph break occurred in the following user code:\n"
                            f"{user_stack_formatted}"
                        )
                        torch._logging.trace_structured(
                            "artifact",
                            metadata_fn=lambda: {
                                "name": "dynamo_graph_break_reason",
                                "encoding": "string",
                            },
                            payload_fn=lambda: f"{user_stack_trace}\n{traceback.format_exc()}",
                        )
                        graph_break_log.debug(
                            user_stack_trace,
                            exc_info=True,
                            stack_info=config.verbose,
                        )

            if not config.suppress_errors and not soft_fail:
                raise

            # Suppress the error.  NB: It's very important to do the
            # suppression logging HERE, where the actual suppression
            # happens. Previously it was somewhere else and so it was
            # possible to accidentally not log at all.
            record_filename = getattr(e, "record_filename", None)
            code = frame.f_code
            error_msg = format_error_msg(e, code, record_filename, frame)

            if soft_fail:
                log.info(error_msg, exc_info=True)
            else:
                log.warning(error_msg, exc_info=True)

            # Check if the exception has a specific frame execution strategy
            if (
                isinstance(e, exc.TorchDynamoException)
                and e.frame_exec_strategy is not None
            ):
                return ConvertFrameReturn(frame_exec_strategy=e.frame_exec_strategy)

        return ConvertFrameReturn()