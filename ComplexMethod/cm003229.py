def _decode_with_timestamps(
        self, token_ids, skip_special_tokens=False, time_precision=0.02, segment_size=1500
    ) -> str:
        """
        Timestamp tokens are above the special tokens' id range and are ignored by `decode()`. This method decodes
        given tokens with timestamps tokens annotated, e.g. "<|1.08|>".
        """
        timestamp_begin = self.all_special_ids[-1] + 1
        outputs = [[]]

        cur_max_timestamp = 0.0
        prev_segments_len = 0.0
        penultimate_timestamp = 0.0

        for i, token in enumerate(token_ids):
            if token >= timestamp_begin:
                timestamp = float((token - timestamp_begin) * time_precision)

                if timestamp < cur_max_timestamp:
                    # next segment has started
                    last_was_single_ending = i >= 2 and not (
                        token_ids[i - 1] >= timestamp_begin and token_ids[i - 2] >= timestamp_begin
                    )
                    if last_was_single_ending:
                        prev_segments_len += time_precision * segment_size
                    else:
                        cur_max_timestamp = penultimate_timestamp
                        prev_segments_len += penultimate_timestamp
                        outputs = outputs[:-2]

                penultimate_timestamp = cur_max_timestamp
                cur_max_timestamp = timestamp

                outputs.append(f"<|{(timestamp + prev_segments_len):.2f}|>")
                outputs.append([])
            else:
                outputs[-1].append(token)
        # Decode token sequences outside list comprehension to avoid super() resolution issues
        decoded_outputs = []
        for s in outputs:
            if isinstance(s, str):
                decoded_outputs.append(s)
            elif s:
                decoded_outputs.append(super().decode(s, skip_special_tokens=skip_special_tokens))
            else:
                decoded_outputs.append("")
        return "".join(decoded_outputs)