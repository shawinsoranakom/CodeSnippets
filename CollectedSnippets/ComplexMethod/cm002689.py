def forward_hook(self, module, input, output):
        # - input is a tuple of packed inputs (could be non-Tensors)
        # - output could be a Tensor or a tuple of Tensors and non-Tensors

        last_frame_of_batch = False

        trace_mode = self.batch_number in self.trace_batch_nums
        if trace_mode:
            self.reset_saved_frames()

        if self.total_calls == 0:
            self.batch_start_frame()
        self.total_calls += 1

        # count batch numbers - the very first forward hook of the batch will be called when the
        # batch completes - i.e. it gets called very last - we know this batch has finished
        if module == self.model:
            self.batch_number += 1
            last_frame_of_batch = True

        self.create_frame(module, input, output)

        # if last_frame_of_batch:
        #     self.batch_end_frame()

        if trace_mode:
            self.trace_frames()

        if last_frame_of_batch:
            self.batch_start_frame()

        if self.detected_overflow and not trace_mode:
            self.dump_saved_frames()

            # now we can abort, as it's pointless to continue running
            raise ValueError(
                "DebugUnderflowOverflow: inf/nan detected, aborting as there is no point running further. "
                "Please scroll up above this traceback to see the activation values prior to this event."
            )

        # abort after certain batch if requested to do so
        if self.abort_after_batch_num is not None and self.batch_number > self.abort_after_batch_num:
            raise ValueError(
                f"DebugUnderflowOverflow: aborting after {self.batch_number} batches due to"
                f" `abort_after_batch_num={self.abort_after_batch_num}` arg"
            )