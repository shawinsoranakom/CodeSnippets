def _compute_offsets(self, token_ids, time_precision=0.02, segment_size=1500):
        """
        Compute offsets for a given tokenized input

        Args:
            token_ids (`Union[int, list[int], np.ndarray, torch.Tensor]`):
                List of tokenized input ids. Can be obtained using the `__call__` method.
            time_precision (`float`, *optional*, defaults to 0.02):
                The time ratio to convert from token to time.
            segment_size (`int`, *optional*, defaults to 1500):
                The number of features in the input mel spectrogram.
        """
        offsets = []
        # ensure torch tensor of token ids is placed on cpu
        if "torch" in str(type(token_ids)) and (hasattr(token_ids, "cpu") and callable(token_ids.cpu)):
            token_ids = token_ids.cpu()
        token_ids = np.array(token_ids)
        if token_ids.shape[0] > 1 and len(token_ids.shape) > 1:
            raise ValueError("Can only process a single input at a time")
        timestamp_begin = self.all_special_ids[-1] + 1
        timestamp_tokens = token_ids >= timestamp_begin

        consecutive = np.where(timestamp_tokens[:-1] & timestamp_tokens[1:])[0] + 1
        if consecutive.shape[0] == 0 and timestamp_tokens.sum() <= 1:
            # either there are no timestamps or there are no consecutive ones
            return []
        elif np.where(timestamp_tokens)[0][-1] + 1 not in consecutive:
            # we add the final timestamp if it is not already in the list
            consecutive = np.append(consecutive, np.where(timestamp_tokens)[0][-1] + 1)

        last_slice = np.where(timestamp_tokens)[0][0]
        cur_max_timestamp = 0
        prev_segments_len = 0
        for current_slice in consecutive:
            sliced_tokens = token_ids[last_slice:current_slice]
            if len(sliced_tokens) > 1:
                start_timestamp_position = sliced_tokens[0].item() - timestamp_begin
                end_timestamp_position = sliced_tokens[-1].item() - timestamp_begin

                if start_timestamp_position < cur_max_timestamp:
                    # next segment has started
                    is_single_ending = last_slice >= 2 and not (
                        token_ids[last_slice - 2] >= timestamp_begin and token_ids[last_slice - 1] >= timestamp_begin
                    )
                    if is_single_ending:
                        prev_segments_len += segment_size
                    else:
                        prev_segments_len += cur_max_timestamp

                cur_max_timestamp = end_timestamp_position

                # strip timestamp tokens from the text output
                sliced_tokens = self._preprocess_token_ids(sliced_tokens)
                text = self._decode(sliced_tokens)
                text = self._filter_timestamp_ids(text)
                offsets.append(
                    {
                        "text": text,
                        "timestamp": (
                            start_timestamp_position * time_precision + prev_segments_len * time_precision,
                            end_timestamp_position * time_precision + prev_segments_len * time_precision,
                        ),
                    }
                )
            last_slice = current_slice

        return offsets