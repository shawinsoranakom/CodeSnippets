def add_text(self, delta_text: str) -> DeltaMessage | None:
        # we start by adding the delta text to the buffer
        self.buffer += delta_text

        # setting this to empty before starting
        delta_message: DeltaMessage | None = None

        # we start by computing the overlap between the delta_text
        # and start/end of think tokens.
        _, overlap_think_start = string_overlap(delta_text, self.think_start)
        _, overlap_think_end = string_overlap(delta_text, self.think_end)

        partial_overlap_start = overlap_think_start is not None and len(
            overlap_think_start
        ) < len(self.think_start)
        partial_overlap_end = overlap_think_end is not None and len(
            overlap_think_end
        ) < len(self.think_end)

        if (
            partial_overlap_start
            and self.think_start in self.buffer
            and not partial_overlap_end
        ):
            # we can only process the buffer if partial overlap
            # is the last part of think token (thus causing
            # text_buffer to contain the start of think token)
            # and there are no partial overlaps with end think
            delta_message = self.process_buffer()

        elif partial_overlap_end and self.think_end in self.buffer:
            # same as before (partial overlap only allowed)
            # if the buffer contains the end think token,
            # but we don't have to check for partial overlap
            # with start think token because they are handled
            # by the previous condition
            delta_message = self.process_buffer()

        elif partial_overlap_start or partial_overlap_end:
            # in general, if there are overlaps, we don't
            # process the buffer because we want to wait until
            # the think token is fully completed.
            return None
        else:
            # we process the buffer as normal
            delta_message = self.process_buffer()

        return delta_message