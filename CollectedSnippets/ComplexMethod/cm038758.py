def sample(
        self,
        tokenizer: TokenizerLike,
        num_requests: int,
        request_id_prefix: str = "",
        no_oversample: bool = False,
        output_len: int | None = None,
        enable_multimodal_chat: bool = False,
        **kwargs,
    ) -> list[SampleRequest]:
        # Filter examples with at least 2 conversations
        filtered_data = self.data.filter(lambda x: len(x["conversations"]) >= 2)
        sampled_requests: list[SampleRequest] = []
        ind = 0
        dynamic_output = output_len is None

        for item in filtered_data:
            if len(sampled_requests) >= num_requests:
                break
            conv = item["conversations"]
            prompt, completion = conv[0]["value"], conv[1]["value"]

            prompt_ids = tokenizer(prompt).input_ids
            completion_ids = tokenizer(completion).input_ids
            prompt_len = len(prompt_ids)
            completion_len = len(completion_ids)
            output_len = completion_len if dynamic_output else output_len
            assert isinstance(output_len, int) and output_len > 0
            if dynamic_output and not is_valid_sequence(prompt_len, completion_len):
                continue
            mm_content = process_image(item["image"]) if "image" in item else None
            if enable_multimodal_chat:
                # Note: when chat is enabled the request prompt_len is no longer
                # accurate and we will be using request output to count the
                # actual prompt len and output len
                prompt = self.apply_multimodal_chat_transformation(prompt, mm_content)
            sampled_requests.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=prompt_len,
                    expected_output_len=output_len,
                    multi_modal_data=mm_content,
                    request_id=request_id_prefix + str(ind),
                )
            )
            ind += 1
        self.maybe_oversample_requests(
            sampled_requests, num_requests, request_id_prefix, no_oversample
        )
        return sampled_requests