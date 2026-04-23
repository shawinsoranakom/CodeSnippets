def _iter_all_frames(self, stack_frames, skip_idle=False):
        for interpreter_info in stack_frames:
            for thread_info in interpreter_info.threads:
                # skip_idle now means: skip if thread is not actively running
                # A thread is "active" if it has the GIL OR is on CPU
                if skip_idle:
                    status_flags = thread_info.status
                    has_gil = bool(status_flags & THREAD_STATUS_HAS_GIL)
                    on_cpu = bool(status_flags & THREAD_STATUS_ON_CPU)
                    if not (has_gil or on_cpu):
                        continue
                frames = thread_info.frame_info
                if frames:
                    # Filter out internal profiler frames from the bottom of the stack
                    frames = self._filter_internal_frames(frames)
                    if frames:
                        yield frames, thread_info.thread_id