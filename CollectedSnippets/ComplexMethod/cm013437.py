def _filter_traceback_frames(
        self, user_stack_summary: traceback.StackSummary
    ) -> traceback.StackSummary:
        # This method can be overridden to customize the frame filtering logic
        # for the recorded stack trace
        user_frames: list[traceback.FrameSummary] = []
        if self._record_forward_stack_traces_only:
            user_frames = [
                frame
                for frame in user_stack_summary
                if (
                    frame.name == "forward"
                    or frame.filename.endswith("torch/__init__.py")
                )
            ]
        else:
            first_forward = -1
            for i, frame in enumerate(user_stack_summary):
                if frame.name == "forward":
                    user_frames = user_stack_summary[i:]
                    first_forward = i
                    break

            # Not having a "forward" call in the stacktrace implies the
            # stacktrace will probably be irrelevant
            if first_forward == -1:
                user_frames: list[traceback.FrameSummary] = []

        from torch.fx.experimental.symbolic_shapes import uninteresting_files

        user_frames = [
            frame
            for frame in user_frames
            if frame.filename not in uninteresting_files()
        ]

        return traceback.StackSummary.from_list(user_frames)