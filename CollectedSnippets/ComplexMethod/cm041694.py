def __call__(self, features: list[dict[str, Any]]) -> dict[str, "torch.Tensor"]:
        batch_images, batch_videos, batch_audios = [], [], []
        batch_imglens, batch_vidlens, batch_audlens, batch_input_ids = [], [], [], []
        packing_params_list: list[dict[str, Any] | None] = []
        for feature in features:
            images = feature.pop("images", None) or []
            videos = feature.pop("videos", None) or []
            audios = feature.pop("audios", None) or []
            batch_images.extend(images)
            batch_videos.extend(videos)
            batch_audios.extend(audios)
            batch_imglens.append(len(images))
            batch_vidlens.append(len(videos))
            batch_audlens.append(len(audios))
            batch_input_ids.append(feature["input_ids"])
            packing_params_list.append(feature.pop("packing_params", None))

        fake_input_ids = []
        has_dummy_image = False
        if (
            self.template.mm_plugin.image_token is not None and sum(batch_imglens) == 0 and sum(batch_vidlens) == 0
        ):  # avoid process hanging in zero3/fsdp case
            fake_messages = [{"role": "user", "content": IMAGE_PLACEHOLDER}]
            fake_images = [Image.new("RGB", (64, 64), (255, 255, 255))]
            fake_messages = self.template.mm_plugin.process_messages(
                fake_messages, fake_images, [], [], self.processor
            )
            _fake_input_ids = self.tokenizer.encode(fake_messages[0]["content"], add_special_tokens=False)
            _fake_input_ids, _ = self.template.mm_plugin.process_token_ids(
                _fake_input_ids, None, fake_images, [], [], self.tokenizer, self.processor
            )
            fake_input_ids.extend(_fake_input_ids)
            batch_images = fake_images
            batch_imglens[0] = 1
            has_dummy_image = True

        if (
            self.template.mm_plugin.audio_token is not None and sum(batch_audlens) == 0
        ):  # avoid process hanging in zero3/fsdp case
            fake_messages = [{"role": "user", "content": AUDIO_PLACEHOLDER}]
            fake_audios = [np.zeros(1600)]
            fake_messages = self.template.mm_plugin.process_messages(
                fake_messages, [], [], fake_audios, self.processor
            )
            _fake_input_ids = self.tokenizer.encode(fake_messages[0]["content"], add_special_tokens=False)
            _fake_input_ids, _ = self.template.mm_plugin.process_token_ids(
                _fake_input_ids, None, [], [], fake_audios, self.tokenizer, self.processor
            )
            fake_input_ids.extend(_fake_input_ids)
            batch_audios = fake_audios
            batch_audlens[0] = 1

        if len(fake_input_ids) != 0:
            if self.tokenizer.padding_side == "right":
                features[0]["input_ids"] = features[0]["input_ids"] + fake_input_ids
                features[0]["attention_mask"] = features[0]["attention_mask"] + [0] * len(fake_input_ids)
                features[0]["labels"] = features[0]["labels"] + [IGNORE_INDEX] * len(fake_input_ids)
            else:
                features[0]["input_ids"] = fake_input_ids + features[0]["input_ids"]
                features[0]["attention_mask"] = [0] * len(fake_input_ids) + features[0]["attention_mask"]
                features[0]["labels"] = [IGNORE_INDEX] * len(fake_input_ids) + features[0]["labels"]

            batch_input_ids[0] = features[0]["input_ids"]

        mm_inputs = self.template.mm_plugin.get_mm_inputs(
            batch_images,
            batch_videos,
            batch_audios,
            batch_imglens,
            batch_vidlens,
            batch_audlens,
            batch_input_ids,
            self.processor,
        )
        if "token_type_ids" in mm_inputs:
            token_type_ids = mm_inputs.pop("token_type_ids")
            for i, feature in enumerate(features):
                feature["token_type_ids"] = token_type_ids[i]

        if "mm_token_type_ids" in mm_inputs: # need tensor-like for gemma4
            mm_token_type_ids = mm_inputs.pop("mm_token_type_ids")
            max_len = max(len(ids) for ids in mm_token_type_ids)
            padded = []
            for ids in mm_token_type_ids:
                pad_len = max_len - len(ids)
                if self.tokenizer.padding_side == "right":
                    padded.append(ids + [0] * pad_len)
                else:
                    padded.append([0] * pad_len + ids)

            mm_inputs["mm_token_type_ids"] = torch.tensor(padded, dtype=torch.long)

        features: dict[str, torch.Tensor] = super().__call__(features)

        bsz, seq_len = features["input_ids"].shape[:2]
        model_type = getattr(self.model.config, "model_type", None) if self.model is not None else None
        is_omni = model_type in [
            "qwen2_5_omni_thinker",
            "qwen3_omni_moe_thinker",
        ]

        if self.get_rope_func is not None:
            # for mmrope situation, we should calculate position_ids and rope_deltas per sample.
            # When neat_packing is on, each sample has packing_params; None means no packing for that sample.
            boundaries_list = [
                p.get("sequence_boundaries") if p is not None else None for p in packing_params_list
            ]
            has_packing = any(b is not None and len(b) > 2 for b in boundaries_list)
            if has_dummy_image and has_packing:
                # FIXME: too tricky, need to be refactored
                features["has_dummy_image"] = True

            # When fake image/audio was injected, sequence_boundaries no longer match the tensor; use non-packing path.
            if not has_packing:
                self._compute_rope_position_ids(features, mm_inputs)
            else:
                if is_omni:
                    raise RuntimeError("Omni models are not supported for packed sequences for now.")

                self._compute_rope_position_ids_with_packing(
                    features,
                    mm_inputs,
                    packing_params_list,
                    batch_imglens,
                    batch_vidlens,
                    batch_audlens,
                    has_dummy_image,
                )

            # For transformers compatibility, after https://github.com/huggingface/transformers/issues/39400
            if features["position_ids"].dim() == 3:
                features["position_ids"] = torch.cat(
                    [features["position_ids"][0].unsqueeze(0), features["position_ids"]], dim=0
                )

        if (
            self.model is not None
            and getattr(self.model.config, "model_type", None) in MROPE_MODELS
            and ("position_ids" not in features or features["position_ids"].dim() != 3)
        ):
            raise ValueError(f"{self.model.config.model_type} requires 3D position ids for mrope.")

        if "cross_attention_mask" in mm_inputs:  # for mllama inputs when pad_to_multiple_of is enabled
            cross_attention_mask = mm_inputs.pop("cross_attention_mask")
            seq_len = features["input_ids"].size(1)
            orig_len = cross_attention_mask.size(1)
            mm_inputs["cross_attention_mask"] = F.pad(cross_attention_mask, (0, 0, 0, 0, 0, seq_len - orig_len))

        features.update(mm_inputs)

        if "image_bound" in features:  # for minicpmv inputs
            bsz, seq_length = features["input_ids"].shape
            features["position_ids"] = torch.arange(seq_length).long().repeat(bsz, 1)
            return {"data": features, "input_ids": features["input_ids"], "labels": features["labels"]}

        return features