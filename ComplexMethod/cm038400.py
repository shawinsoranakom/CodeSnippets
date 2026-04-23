def _tool_extraction_step(
        self,
        delta_text: str,
    ) -> tuple[bool, str, str]:
        start_token_pos = start_token_end = end_token_pos = end_token_end = -1

        if start_match := self.start_regex.search(delta_text, partial=True):
            if not start_match.partial:
                start_token_pos, start_token_end = start_match.span()
            elif start_match.end() > start_match.start():
                start_token_pos = -2

        if end_match := self.end_regex.search(delta_text):
            end_token_pos, end_token_end = end_match.span()

        # Done means that we've exhausted the current buffer
        # and need more output from the model
        done = True
        content = tc_text = ""

        if start_token_pos < 0:
            # just streaming text so far
            if start_token_pos == -2:
                # There is a partial match
                content = delta_text[: start_match.start()]
                self.look_ahead = delta_text[start_match.start() :]
            else:
                content = delta_text

        elif not self.in_tc:
            # we're entering a new tool call
            self.in_tc = True

            content = delta_text[:start_token_pos]
            if end_token_pos > 0:
                self.start_in_tc = False
                tc_text = delta_text[start_token_end:end_token_pos]
                self.look_ahead = delta_text[end_token_end:]
                done = False  # There could be more content already buffered
            else:
                self.look_ahead = delta_text[start_token_pos:]

        elif end_token_pos < 0:
            # we're in between the start and the end token
            assert self.in_tc
            self.look_ahead = delta_text
        else:
            # We have found the end
            assert self.in_tc
            tc_text = delta_text[start_token_end:end_token_pos]
            self.in_tc = False
            self.look_ahead = delta_text[end_token_end:]
            done = False  # There could be more content already buffered
        return done, content, tc_text