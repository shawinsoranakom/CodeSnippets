def log_graph_break(
        self,
        code_options: dict[str, Any],
        reason: str,
        exc: Unsupported | UserError | StepUnsupported,
    ) -> None:
        if exc.logged:
            return

        user_stack = getattr(exc, "real_stack", None)

        if user_stack is None:
            user_stack = torch._guards.TracingContext.extract_stack()

        try:
            if config.nested_graph_breaks and self.parent is not None:
                frame_loc = self._make_frame_loc(
                    self.f_code.co_filename,
                    self.lineno,
                    self.f_code.co_firstlineno,
                )
            else:
                frame_loc = self._make_frame_loc(
                    user_stack[-1].filename,
                    user_stack[-1].lineno,
                    0,
                )
        except IndexError:
            # first instruction
            frame_loc = (
                code_options["co_filename"],
                code_options["co_firstlineno"],
            )
        frame_loc_chain = self._get_frame_loc_chain(frame_loc)
        stack_above_dynamo_formatted = ""
        if config.verbose:
            stack_above_dynamo = get_stack_above_dynamo()
            stack_above_dynamo_formatted = "".join(
                traceback.format_list(stack_above_dynamo)
            )
        else:
            user_stack = get_stack_above_dynamo() + user_stack  # type: ignore[assignment]
            user_stack = collapse_resume_frames(user_stack)
        user_stack_formatted = "".join(traceback.format_list(user_stack))

        # Add HOP context after the first line of reason if present
        if exc is not None:
            reason = augment_exc_message_with_hop_name(exc, reason)

        stack_source_attribution = self._format_stack_source_attribution()
        user_stack_trace_parts = [
            f"Graph break in user code at {frame_loc[0]}:{frame_loc[1]}",
            f"Graph Break Reason: {reason}",
        ]
        if stack_source_attribution:
            user_stack_trace_parts.extend(["", stack_source_attribution])
        user_stack_trace_parts.extend(["", "User code traceback:"])
        user_stack_trace = "\n".join(user_stack_trace_parts) + "\n"

        if config.verbose:
            user_stack_trace += (
                f"{stack_above_dynamo_formatted}\n"
                "========== most recent `torch.compile` tracing attempt started here ==========\n\n"
                f"{user_stack_formatted}\n"
                "NOTE: the most recent `torch.compile` tracing attempt might not be where you applied `torch.compile`! "
                "This is due to how graph breaks are implemented - the optimized code object returned by Dynamo will call another "
                "Dynamo-generated resume function and tracing is re-enabled by calling the resume function as a normal Python "
                "function, which Dynamo intercepts as a top-level frame.\n"
            )
        else:
            user_stack_trace += str(user_stack_formatted)

        torch._logging.trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "dynamo_graph_break_reason",
                "encoding": "string",
            },
            payload_fn=lambda: f"{user_stack_trace}\n{traceback.format_exc()}",
        )

        # torch._dynamo.explain() formats this a little nicer, and presents a slightly
        # more actionable user code pointer
        gb_type = exc.gb_type if isinstance(exc, Unsupported) else type(exc)
        if (
            graph_break_log.isEnabledFor(logging.DEBUG)
            and not explain
            and graph_break_dup_warning_checker.add((gb_type, frame_loc_chain))  # type: ignore[arg-type]
        ):
            # This log line MUST contain the string "Graph break in user code",
            # This log line is exercised from
            #   python test/dynamo/test_exc.py -k test_graph_break_log
            if config.verbose:
                user_stack_trace += (
                    "\nMost recent bytecode instructions traced (max 20):\n"
                )
                user_stack_trace += "\n".join(self.latest_bytecode_queue) + "\n"

            graph_break_log.debug(
                user_stack_trace,
            )
        else:
            # This log line MUST not contain the string "Graph break in user code",
            # exercised by
            #   python test/dynamo/test_misc.py -k test_duplicate_graph_break_log
            graph_break_log.debug(
                "Graph break (user stack suppressed due to duplicate graph break) in user code at %s:%s\nGraph Break Reason: %s",
                frame_loc[0],
                frame_loc[1],
                reason,
            )

        exc.logged = True