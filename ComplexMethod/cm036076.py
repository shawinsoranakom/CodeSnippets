def generate_prompt_perplexity(
        self, prompts: list[str], mask: Optional[list[str]] = None
    ) -> list[float]:
        """
        Return the perplexity score associated with generating the prompts

        :param prompts: list of prompts to score
        :return: perplexity score of each prompt
        """
        outputs = self.generate_greedy_logprobs(
            prompts, max_tokens=1, num_logprobs=None, num_prompt_logprobs=0
        )

        mask_prefix_lens = (
            [len(self.llm.get_tokenizer()(prefix)["input_ids"]) for prefix in mask]
            if mask is not None
            else [0 for _ in range(len(prompts))]
        )

        perplexities = []
        for output, mask_prefix_len in zip(outputs, mask_prefix_lens):
            output = cast(TokensTextLogprobsPromptLogprobs, output)
            token_datas = cast(list[dict[int, Logprob] | None], output[3])
            assert token_datas[0] is None

            token_log_probs = []
            for token_data in token_datas[mask_prefix_len + 1 :]:
                assert token_data is not None
                assert len(token_data) == 1
                token_log_prob = list(token_data.values())[0].logprob
                token_log_probs.append(token_log_prob)

            perplexity = math.exp(-sum(token_log_probs) / len(token_log_probs))
            perplexities.append(perplexity)

        return perplexities