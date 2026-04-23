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
        lora_assignment: str = "random",
        **kwargs,
    ) -> list[SampleRequest]:
        samples: list[SampleRequest] = []
        ind = 0
        for entry in self.data:
            if len(samples) >= num_requests:
                break
            prompt, completion = (
                entry["conversations"][0]["value"],
                entry["conversations"][1]["value"],
            )

            lora_request = self.get_lora_request(
                index=ind,
                max_loras=max_loras,
                lora_path=lora_path,
                lora_assignment=lora_assignment,
            )
            prompt_ids = tokenizer(prompt).input_ids
            completion_ids = tokenizer(completion).input_ids
            prompt_len = len(prompt_ids)
            new_output_len = len(completion_ids) if output_len is None else output_len
            if not is_valid_sequence(
                prompt_len,
                new_output_len,
                skip_min_output_len_check=output_len is not None,
            ):
                continue
            if image_path := entry.get("image"):
                mm_content = process_image(image_path)
            elif video_path := entry.get("video"):
                mm_content = process_video(video_path)
            else:
                mm_content = None
            if enable_multimodal_chat:
                prompt = self.apply_multimodal_chat_transformation(prompt, mm_content)
            samples.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=prompt_len,
                    expected_output_len=new_output_len,
                    lora_request=lora_request,
                    multi_modal_data=mm_content,
                    request_id=request_id_prefix + str(ind),
                )
            )
            ind += 1
        self.maybe_oversample_requests(
            samples, num_requests, request_id_prefix, no_oversample
        )
        return samples