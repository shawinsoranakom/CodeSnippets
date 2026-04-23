def update_candidate_strategy(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, num_matches: int):
        """
        Updates the candidate generation strategy based on the outcomes.

        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary. [What are input IDs?](../glossary#input-ids)
            scores (`torch.FloatTensor` of shape `(batch_size, candidate_length, config.vocab_size)`):
                Prediction scores of a language modeling head. These can be logits for each vocabulary when not using
                beam search or log softmax for each vocabulary token when using beam search
            num_matches (`int`):
                The number of matches between the candidate sequences and the model predictions.
        """
        # Adjust the max number of assistant tokens to use in the next iteration. This is a simple heuristic,
        # probably can be improved -- we want to balance the benefits of getting assistant tokens correct with the
        # cost of forecasting incorrect assistant tokens.
        if self.assistant_generation_config.num_assistant_tokens_schedule in {
            "heuristic",
            "heuristic_transient",
        }:
            # len(scores[0])-1 is the number of candidates according to the target tokenizer.
            if num_matches == len(scores[0]) - 1:
                self.num_assistant_tokens += 2
            else:
                self.num_assistant_tokens = max(1, self.num_assistant_tokens - 1)

        # The assistant's confidence threshold is adjusted throughout the speculative iterations to reduce the number of unnecessary draft and target forward passes. The costs are estimated based on the ROC curve, which considers the probability of the draft token and its match with the target. A cost of 25% is assigned to false positives and 75% to false negatives.
        # This adaptation is not compatible with UAG, as it relies on the number of matched tokens based on the draft vocabulary, which is unavailable in UAG.
        if (
            is_sklearn_available()
            and self.assistant_generation_config.assistant_confidence_threshold
            and type(self) is AssistedCandidateGenerator
        ):
            # update self.matches
            self.matches.extend([1] * num_matches)
            if len(self.probs) > len(self.matches):
                self.matches.append(0)

            # update self.probs
            excess_length = len(self.probs) - len(self.matches)
            if excess_length > 0:
                del self.probs[-excess_length:]

            if (
                len(self.probs) > 5 and {0, 1}.issubset(self.matches)
            ):  # require at least 5 samples to calculate the ROC curve and at least one positive and one negative sample
                fpr, tpr, thresholds = roc_curve(self.matches, self.probs)
                fnr = 1 - tpr

                # Calculate the cost for each threshold
                costs = fpr + 3 * fnr

                # Find the threshold that minimizes the cost
                optimal_threshold_index = np.argmin(costs)
                best_threshold = thresholds[optimal_threshold_index]

                self.assistant_generation_config.assistant_confidence_threshold = best_threshold