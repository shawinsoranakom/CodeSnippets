def sample(
        self,
        tokenizer: TokenizerLike,
        num_requests: int,
        request_id_prefix: str = "",
        no_oversample: bool = False,
        lora_path: str | None = None,
        max_loras: int | None = None,
        output_len: int | None = None,
        enable_multimodal_chat: bool = False,
        skip_chat_template: bool = False,
        **kwargs,
    ) -> list[SampleRequest]:
        # load all data if needed
        self.num_available_samples = len(self.data)
        if num_requests <= 0:
            num_requests = self.num_available_samples
            logger.info(
                "num_requests is set to 0 or negative, "
                "so using all available samples: %d",
                num_requests,
            )

        sampled_requests: list[SampleRequest] = []
        for i, item in enumerate(self.data):
            if len(sampled_requests) >= num_requests:
                break
            prompt = item["prompt"]

            if tokenizer is None:
                new_output_len = 1
            else:
                new_output_len = output_len
                if output_len is None or output_len == -1:
                    # check that the request has an 'output_tokens' field
                    if "output_tokens" not in item:
                        raise ValueError(
                            "If no output length is provided the "
                            "custom dataset must contain an 'output_tokens' field."
                        )
                    # Use number of output tokens from the request data
                    try:
                        new_output_len = int(item["output_tokens"])
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Invalid value for 'output_tokens' in custom dataset: "
                            f"'{item['output_tokens']}'. Must be an integer."
                        ) from e

            if tokenizer is None:
                prompt_len = 1
            else:
                # apply template
                if not skip_chat_template:
                    prompt = tokenizer.apply_chat_template(
                        [{"role": "user", "content": prompt}],
                        add_generation_prompt=True,
                        tokenize=False,
                    )

                prompt_len = len(tokenizer(prompt).input_ids)
            sampled_requests.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=prompt_len,
                    expected_output_len=new_output_len,
                    request_id=request_id_prefix + str(i),
                )
            )
        self.maybe_oversample_requests(
            sampled_requests, num_requests, request_id_prefix, no_oversample
        )

        return sampled_requests