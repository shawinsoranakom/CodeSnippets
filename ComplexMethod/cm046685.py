def _preprocess_snac_dataset(self, dataset, custom_format_mapping = None):
        """Preprocess dataset for Orpheus TTS training with SNAC codec.

        Mirrors Orpheus_(3B)-TTS.ipynb: encode audio with SNAC (24kHz, 3 hierarchical
        layers), interleave 7 codes per frame, wrap with Orpheus special tokens,
        train on full sequence (no label masking).
        """
        import torch
        import torchaudio.transforms as T

        SNAC_MODEL_NAME = "hubertsiuzdak/snac_24khz"
        SNAC_SAMPLE_RATE = 24000
        device = "cuda" if torch.cuda.is_available() else "cpu"
        max_length = self.max_seq_length or 2048
        tokenizer = self.tokenizer

        # Orpheus special token IDs (hardcoded in tokenizer vocabulary)
        START_OF_HUMAN = 128259
        END_OF_HUMAN = 128260
        START_OF_AI = 128261
        END_OF_AI = 128262
        START_OF_SPEECH = 128257
        END_OF_SPEECH = 128258
        END_OF_TEXT = 128009
        AUDIO_OFFSET = 128266

        resolved = self._resolve_audio_columns(dataset, custom_format_mapping)
        audio_col = resolved["audio_col"]
        text_col = resolved["text_col"]
        speaker_col = resolved["speaker_col"]
        has_source = speaker_col is not None
        if not audio_col or not text_col:
            raise ValueError(
                f"SNAC dataset needs 'audio' and 'text' columns, got: {dataset.column_names}"
            )

        # Cast audio column so datasets 4.x AudioDecoder objects are decoded to dicts
        from datasets import Audio

        dataset = dataset.cast_column(audio_col, Audio(sampling_rate = SNAC_SAMPLE_RATE))

        # Get dataset sample rate from first example (after cast, always SNAC_SAMPLE_RATE)
        first_audio = dataset[0][audio_col]
        ds_sample_rate = (
            first_audio.get("sampling_rate", SNAC_SAMPLE_RATE)
            if isinstance(first_audio, dict)
            else SNAC_SAMPLE_RATE
        )

        # Load SNAC codec model
        self._update_progress(status_message = "Loading SNAC codec model...")
        logger.info("Loading SNAC codec model...\n")
        from snac import SNAC

        snac_model = SNAC.from_pretrained(SNAC_MODEL_NAME)
        snac_model = snac_model.to(device).eval()

        # Resample transform (created once)
        resample_transform = (
            T.Resample(orig_freq = ds_sample_rate, new_freq = SNAC_SAMPLE_RATE)
            if ds_sample_rate != SNAC_SAMPLE_RATE
            else None
        )

        self._update_progress(status_message = "Encoding audio with SNAC...")
        logger.info(
            f"SNAC preprocessing: audio_col='{audio_col}', text_col='{text_col}', "
            f"has_source={has_source}, ds_sample_rate={ds_sample_rate}\n"
        )

        processed_examples = []
        skipped = 0
        for idx in range(len(dataset)):
            if self.should_stop:
                logger.info("Stopped during SNAC preprocessing\n")
                break

            example = dataset[idx]
            try:
                text = example.get(text_col)
                if not text:
                    skipped += 1
                    continue

                audio_data = example.get(audio_col)
                if audio_data is None or audio_data.get("array") is None:
                    skipped += 1
                    continue

                # --- Encode audio with SNAC (notebook lines 122-142) ---
                waveform = (
                    torch.from_numpy(audio_data["array"])
                    .unsqueeze(0)
                    .to(dtype = torch.float32)
                )
                if resample_transform is not None:
                    waveform = resample_transform(waveform)

                waveform = waveform.unsqueeze(0).to(device)
                with torch.inference_mode():
                    codes = snac_model.encode(waveform)

                # Interleave 7 codes per frame with layer offsets (notebook lines 134-142)
                all_codes = []
                for i in range(codes[0].shape[1]):
                    all_codes.append(codes[0][0][i].item() + AUDIO_OFFSET)
                    all_codes.append(codes[1][0][2 * i].item() + AUDIO_OFFSET + 4096)
                    all_codes.append(
                        codes[2][0][4 * i].item() + AUDIO_OFFSET + (2 * 4096)
                    )
                    all_codes.append(
                        codes[2][0][(4 * i) + 1].item() + AUDIO_OFFSET + (3 * 4096)
                    )
                    all_codes.append(
                        codes[1][0][(2 * i) + 1].item() + AUDIO_OFFSET + (4 * 4096)
                    )
                    all_codes.append(
                        codes[2][0][(4 * i) + 2].item() + AUDIO_OFFSET + (5 * 4096)
                    )
                    all_codes.append(
                        codes[2][0][(4 * i) + 3].item() + AUDIO_OFFSET + (6 * 4096)
                    )

                if len(all_codes) == 0:
                    skipped += 1
                    continue

                # Deduplicate consecutive frames with same first code (notebook lines 185-207)
                deduped = all_codes[:7]
                for i in range(7, len(all_codes), 7):
                    if all_codes[i] != deduped[-7]:
                        deduped.extend(all_codes[i : i + 7])
                all_codes = deduped

                # --- Build text tokens (notebook lines 217-224) ---
                text_prompt = (
                    f"{example[speaker_col]}: {text}"
                    if has_source and example.get(speaker_col)
                    else text
                )
                text_ids = tokenizer.encode(text_prompt, add_special_tokens = True)
                text_ids.append(END_OF_TEXT)

                # --- Build full input_ids (notebook lines 225-234) ---
                input_ids = (
                    [START_OF_HUMAN]
                    + text_ids
                    + [END_OF_HUMAN]
                    + [START_OF_AI]
                    + [START_OF_SPEECH]
                    + all_codes
                    + [END_OF_SPEECH]
                    + [END_OF_AI]
                )

                # Truncate to max_length
                input_ids = input_ids[:max_length]

                # Labels = input_ids (no masking — Orpheus trains on full sequence)
                labels = list(input_ids)
                attention_mask = [1] * len(input_ids)

                processed_examples.append(
                    {
                        "input_ids": input_ids,
                        "labels": labels,
                        "attention_mask": attention_mask,
                    }
                )

            except Exception as e:
                logger.warning(f"Error processing SNAC example {idx}: {e}")
                skipped += 1
                continue

            # Progress update every 100 examples
            if (idx + 1) % 100 == 0:
                self._update_progress(
                    status_message = f"Encoding audio... {idx + 1}/{len(dataset)}"
                )

        # Free SNAC model from GPU
        logger.info("Freeing SNAC codec model from GPU...\n")
        snac_model.to("cpu")
        del snac_model
        import gc

        gc.collect()
        torch.cuda.empty_cache()
        self._cuda_audio_used = True

        if not processed_examples:
            raise ValueError(
                f"No valid examples after SNAC preprocessing (skipped {skipped})"
            )

        result_dataset = Dataset.from_list(processed_examples)
        logger.info(
            f"SNAC preprocessing complete: {len(result_dataset)} examples "
            f"({skipped} skipped)\n"
        )
        return result_dataset