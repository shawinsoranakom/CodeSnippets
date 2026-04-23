def _apply_prompt_updates(
        self,
        token_ids: list[int],
        mm_prompt_updates: MultiModalPromptUpdates,
    ) -> tuple[list[int], Mapping[str, list[PlaceholderFeaturesInfo]]]:
        # align to hf behavior when there are images
        if len(mm_prompt_updates):
            tokenizer = self.info.get_tokenizer()
            # to decode token_ids to the original text, we need to
            # 1. remove the first bos token
            # 2. remove space after each special token
            #    introduced by the tokenizer
            if len(token_ids) and token_ids[0] == tokenizer.bos_token_id:
                token_ids = token_ids[1:]
            text = tokenizer.decode(token_ids)
            for special_tokens in tokenizer.special_tokens_map.values():
                if isinstance(special_tokens, str):
                    text = text.replace(f"{special_tokens} ", special_tokens)
                elif isinstance(special_tokens, list):
                    for special_token in special_tokens:
                        text = text.replace(f"{special_token} ", special_token)
            # perform hf behavior
            # https://huggingface.co/microsoft/Phi-3.5-vision-instruct/blob/64f88b6/processing_phi3_v.py#L407
            pattern = r"<\|image_\d+\|>"
            prompt_chunks = [
                tokenizer(chunk).input_ids for chunk in re.split(pattern, text)
            ]
            image_tags = [
                tokenizer(chunk, add_special_tokens=False).input_ids
                for chunk in re.findall(pattern, text)
            ]
            if len(prompt_chunks) > len(image_tags):
                image_tags.append([])
            token_ids = [
                e
                for sublist in zip(prompt_chunks, image_tags)
                for ele in sublist
                for e in ele
            ]

        token_ids, placeholders = super()._apply_prompt_updates(
            token_ids=token_ids,
            mm_prompt_updates=mm_prompt_updates,
        )

        # Keep the behavior in line with HF processor
        if len(mm_prompt_updates) and (
            token_ids[:2] == tokenizer.encode("<s> <|image|>", add_special_tokens=False)
        ):
            token_ids = [token_ids[0], *token_ids[2:]]
            placeholders = {
                modality: [
                    PlaceholderFeaturesInfo(
                        modality=p.modality,
                        item_idx=p.item_idx,
                        start_idx=p.start_idx - 1,
                        tokens=p.tokens,
                        is_embed=p.is_embed,
                    )
                    for p in ps
                ]
                for modality, ps in placeholders.items()
            }

        return token_ids, placeholders