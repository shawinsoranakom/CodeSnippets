def _preprocess_csm_dataset(self, dataset, custom_format_mapping = None):
        """Preprocess dataset for CSM TTS training (exact notebook copy)."""
        from transformers import AutoProcessor
        from datasets import Audio
        import torch

        processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code = getattr(self, "trust_remote_code", False),
        )

        # Strip pad_to_multiple_of from tokenizer init_kwargs — fine-tuned models
        # (e.g. keanteng/sesame-csm-elise) save it in tokenizer_config.json, and
        # _merge_kwargs leaks it into audio_kwargs where EncodecFeatureExtractor rejects it.
        processor.tokenizer.init_kwargs.pop("pad_to_multiple_of", None)

        # Resolve columns from user mapping or hardcoded fallback
        resolved = self._resolve_audio_columns(dataset, custom_format_mapping)
        audio_col = resolved["audio_col"]
        text_col = resolved["text_col"]
        speaker_key = resolved["speaker_col"]

        if audio_col is None:
            raise ValueError(
                f"No audio column found in dataset. Columns: {dataset.column_names}"
            )
        if text_col is None:
            raise ValueError(
                f"No text column found in dataset. Columns: {dataset.column_names}"
            )
        if speaker_key is None:
            logger.info(
                "No speaker found, adding default 'source' of 0 for all examples\n"
            )
            dataset = dataset.add_column("source", ["0"] * len(dataset))
            speaker_key = "source"

        logger.info(
            f"CSM preprocessing: audio_col='{audio_col}', text_col='{text_col}', speaker_key='{speaker_key}'\n"
        )

        dataset = dataset.cast_column(audio_col, Audio(sampling_rate = 24000))

        required_keys = [
            "input_ids",
            "attention_mask",
            "labels",
            "input_values",
            "input_values_cutoffs",
        ]

        self._update_progress(status_message = "Preprocessing CSM dataset...")
        processed_examples = []
        skipped = 0
        for idx in range(len(dataset)):
            if self.should_stop:
                logger.info("Stopped during CSM preprocessing\n")
                break

            example = dataset[idx]
            try:
                conversation = [
                    {
                        "role": str(example[speaker_key]),
                        "content": [
                            {"type": "text", "text": example.get(text_col, "")},
                            {"type": "audio", "path": example[audio_col]["array"]},
                        ],
                    }
                ]
                # NOTE: pad_to_multiple_of intentionally omitted from text_kwargs —
                # CsmProcessor._merge_kwargs leaks it to EncodecFeatureExtractor which rejects it.
                model_inputs = processor.apply_chat_template(
                    conversation,
                    tokenize = True,
                    return_dict = True,
                    output_labels = True,
                    text_kwargs = {
                        "padding": "max_length",
                        "max_length": 256,
                        "padding_side": "right",
                    },
                    audio_kwargs = {
                        "sampling_rate": 24_000,
                        "max_length": 240001,
                        "padding": "max_length",
                    },
                    common_kwargs = {"return_tensors": "pt"},
                )

                out = {}
                for k in required_keys:
                    if k not in model_inputs:
                        raise KeyError(f"Missing required key '{k}' in model outputs")
                    out[k] = model_inputs[k][0]

                if not all(isinstance(out[k], torch.Tensor) for k in out):
                    skipped += 1
                    continue

                processed_examples.append(out)

            except Exception as e:
                logger.warning(f"Error processing CSM example {idx}: {e}")
                skipped += 1
                continue

            if (idx + 1) % 100 == 0:
                self._update_progress(
                    status_message = f"Preprocessing CSM... {idx + 1}/{len(dataset)}"
                )

        if not processed_examples:
            raise ValueError(
                f"No valid examples after CSM preprocessing (skipped {skipped})"
            )

        result_dataset = Dataset.from_list(processed_examples)
        logger.info(
            f"CSM preprocessing complete: {len(result_dataset)} examples "
            f"({skipped} skipped)\n"
        )
        return result_dataset