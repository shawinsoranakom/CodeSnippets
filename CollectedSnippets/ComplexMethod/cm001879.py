def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
            # we don't want to randomly sample timestamp tokens
            if input_ids.shape[-1] != self.begin_index:
                scores[:, self.timestamp_begin :] = -float("inf")

            self.no_time_stamp_counter = [x + 1 for x in self.no_time_stamp_counter]
            for k in range(input_ids.shape[0]):
                # make sure to use correct index if a batch was removed
                if self.is_length_ascending and input_ids.shape[0] < self.batch_size:
                    prev_k = k + self.batch_size - input_ids.shape[0]
                else:
                    prev_k = k

                if input_ids[k, -1] == self.timestamp_begin:
                    self.no_time_stamp_counter[prev_k] = 0

                can_produce = self.no_time_stamp_counter[prev_k] > self.min_space_between_timestamps
                must_produce = (
                    input_ids[k][2:].le(self.timestamp_begin).all() and input_ids.shape[-1] == self.max_length - 1
                )
                # produce timestamp with 30%
                if (can_produce and self.let_pass[prev_k][self.count]) or must_produce:
                    self.no_time_stamp_counter[prev_k] = 0
                    self.prev_highest_timestamp[prev_k] = max(input_ids[k].max() + 1, self.timestamp_tokens[0].item())

                    # force a timestamp
                    scores[k, :] = -float("inf")
                    scores[k, self.prev_highest_timestamp[prev_k]] = 10.0

                if (
                    input_ids.shape[-1] > 3
                    and input_ids[k, -1].item() in self.timestamp_tokens
                    and input_ids[k, -2].item() not in self.timestamp_tokens
                ):
                    # force the same as before
                    scores[k, :] = -float("inf")
                    scores[k, input_ids[k, -1].item()] = 10.0

            self.count += 1

            if torch.isinf(scores).all():
                raise ValueError("Dummy logit processor is incorrectly set up. Scores should not be all inf.")

            return scores