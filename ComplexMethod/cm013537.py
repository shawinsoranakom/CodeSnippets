def _get_stack_summary(
        self, is_debug: bool = False, framework_loc: str | None = None
    ) -> tuple[SLoc, str]:
        floc: str | traceback.FrameSummary | None = framework_loc
        if floc is None:
            frame = self._get_user_frame()
            try:
                if frame is not None:
                    floc = traceback.FrameSummary(
                        frame.f_code.co_filename,
                        frame.f_lineno,
                        frame.f_code.co_name,
                    )
            finally:
                del frame

        # NB: this stack is truncated, but it's fine because the main
        # stack_info will give you the rest of the info you need
        maybe_user_loc = None
        user_tb = TracingContext.extract_stack()
        if user_tb:
            idx = len(user_tb) - 1
            while idx > 0 and user_tb[idx].filename in uninteresting_files():
                idx -= 1
            maybe_user_loc = format_frame(user_tb[idx], line=True)

        maybe_extra_debug = ""
        if is_debug and user_tb:
            maybe_extra_debug = (
                "\nUser Stack (most recent call last):\n"
                + "  (snipped, see stack below for prefix)\n"
                + "".join(traceback.format_list(user_tb))
            )
        if is_debug and config.extended_debug_cpp:
            cpp_stack = CapturedTraceback.extract(cpp=True)
            maybe_extra_debug += "\nC++ stack trace:\n" + "".join(cpp_stack.format())
        elif is_debug:
            maybe_extra_debug += (
                "\nFor C++ stack trace, run with TORCHDYNAMO_EXTENDED_DEBUG_CPP=1"
            )

        return SLoc(floc, maybe_user_loc), maybe_extra_debug