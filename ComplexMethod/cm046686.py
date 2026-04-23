def _preprocess_bicodec_dataset(self, dataset, custom_format_mapping = None):
        """Preprocess dataset for Spark-TTS training with BiCodec tokenizer.

        Mirrors Spark_TTS_(0_5B).ipynb: encode audio with BiCodec (semantic + global tokens),
        format as special-token text strings for SFTTrainer with dataset_text_field="text".
        """
        import sys
        import torch
        import numpy as np
        import torchaudio.transforms as T

        import subprocess

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # The sparktts Python package lives in the SparkAudio/Spark-TTS GitHub repo,
        # NOT in the unsloth/Spark-TTS-0.5B HF model repo. Clone it if needed.
        spark_code_dir = os.path.join(
            os.path.dirname(self._spark_tts_repo_dir), "Spark-TTS"
        )
        sparktts_pkg = os.path.join(spark_code_dir, "sparktts")
        if not os.path.isdir(sparktts_pkg):
            self._update_progress(status_message = "Cloning Spark-TTS code repo...")
            logger.info(f"Cloning SparkAudio/Spark-TTS to {spark_code_dir}...\n")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/SparkAudio/Spark-TTS",
                    spark_code_dir,
                ],
                check = True,
            )

        if spark_code_dir not in sys.path:
            sys.path.insert(0, spark_code_dir)

        from sparktts.models.audio_tokenizer import BiCodecTokenizer
        from sparktts.utils.audio import audio_volume_normalize

        # Resolve audio and text columns
        resolved = self._resolve_audio_columns(dataset, custom_format_mapping)
        audio_col = resolved["audio_col"]
        text_col = resolved["text_col"]
        speaker_col = resolved["speaker_col"]
        has_source = speaker_col is not None
        if not audio_col or not text_col:
            raise ValueError(
                f"BiCodec dataset needs 'audio' and 'text' columns, got: {dataset.column_names}"
            )

        # Cast audio column so datasets 4.x AudioDecoder objects are decoded to dicts.
        # Don't resample here — BiCodec's target_sr may differ; the loop handles resampling.
        from datasets import Audio

        dataset = dataset.cast_column(audio_col, Audio())

        # Load BiCodec tokenizer
        self._update_progress(status_message = "Loading BiCodec tokenizer...")
        logger.info("Loading BiCodec tokenizer...\n")
        audio_tokenizer = BiCodecTokenizer(self._spark_tts_repo_dir, device)

        target_sr = audio_tokenizer.config["sample_rate"]

        self._update_progress(status_message = "Encoding audio with BiCodec...")
        logger.info(
            f"BiCodec preprocessing: audio_col='{audio_col}', text_col='{text_col}', "
            f"has_source={has_source}, target_sr={target_sr}\n"
        )

        def extract_wav2vec2_features(wavs: torch.Tensor) -> torch.Tensor:
            """Extract wav2vec2 features (average of layers 11, 14, 16)."""
            if wavs.shape[0] != 1:
                raise ValueError(f"Expected batch size 1, but got shape {wavs.shape}")
            wav_np = wavs.squeeze(0).cpu().numpy()

            processed = audio_tokenizer.processor(
                wav_np,
                sampling_rate = 16000,
                return_tensors = "pt",
                padding = True,
            )
            input_values = processed.input_values.to(
                audio_tokenizer.feature_extractor.device
            )
            model_output = audio_tokenizer.feature_extractor(input_values)

            if model_output.hidden_states is None:
                raise ValueError("Wav2Vec2Model did not return hidden states.")

            feats_mix = (
                model_output.hidden_states[11]
                + model_output.hidden_states[14]
                + model_output.hidden_states[16]
            ) / 3
            return feats_mix

        processed_examples = []
        skipped = 0
        for idx in range(len(dataset)):
            if self.should_stop:
                logger.info("Stopped during BiCodec preprocessing\n")
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

                audio_array = audio_data["array"]
                sampling_rate = audio_data.get("sampling_rate", target_sr)

                # Resample if needed
                if sampling_rate != target_sr:
                    resampler = T.Resample(orig_freq = sampling_rate, new_freq = target_sr)
                    audio_tensor_temp = torch.from_numpy(audio_array).float()
                    audio_array = resampler(audio_tensor_temp).numpy()

                # Volume normalize if configured
                if audio_tokenizer.config.get("volume_normalize", False):
                    audio_array = audio_volume_normalize(audio_array)

                # Get reference clip
                ref_wav_np = audio_tokenizer.get_ref_clip(audio_array)

                # Prepare tensors
                audio_tensor = (
                    torch.from_numpy(audio_array).unsqueeze(0).float().to(device)
                )
                ref_wav_tensor = (
                    torch.from_numpy(ref_wav_np).unsqueeze(0).float().to(device)
                )

                # Extract wav2vec2 features
                feat = extract_wav2vec2_features(audio_tensor)

                batch = {
                    "wav": audio_tensor,
                    "ref_wav": ref_wav_tensor,
                    "feat": feat.to(device),
                }

                # BiCodec tokenize
                semantic_token_ids, global_token_ids = audio_tokenizer.model.tokenize(
                    batch
                )

                global_tokens = "".join(
                    [
                        f"<|bicodec_global_{i}|>"
                        for i in global_token_ids.squeeze().cpu().numpy()
                    ]
                )
                semantic_tokens = "".join(
                    [
                        f"<|bicodec_semantic_{i}|>"
                        for i in semantic_token_ids.squeeze().cpu().numpy()
                    ]
                )

                # Format text with source prefix if available
                text_content = (
                    f"{example[speaker_col]}: {text}"
                    if has_source and example.get(speaker_col)
                    else text
                )

                formatted = "".join(
                    [
                        "<|task_tts|>",
                        "<|start_content|>",
                        text_content,
                        "<|end_content|>",
                        "<|start_global_token|>",
                        global_tokens,
                        "<|end_global_token|>",
                        "<|start_semantic_token|>",
                        semantic_tokens,
                        "<|end_semantic_token|>",
                        "<|im_end|>",
                    ]
                )

                processed_examples.append({"text": formatted})

            except Exception as e:
                logger.warning(f"Error processing BiCodec example {idx}: {e}")
                skipped += 1
                continue

            # Progress update every 100 examples
            if (idx + 1) % 100 == 0:
                self._update_progress(
                    status_message = f"Encoding audio with BiCodec... {idx + 1}/{len(dataset)}"
                )

        # Free BiCodec model from GPU
        logger.info("Freeing BiCodec tokenizer from GPU...\n")
        audio_tokenizer.model.cpu()
        audio_tokenizer.feature_extractor.cpu()
        del audio_tokenizer
        import gc

        gc.collect()
        torch.cuda.empty_cache()
        self._cuda_audio_used = True

        if not processed_examples:
            raise ValueError(
                f"No valid examples after BiCodec preprocessing (skipped {skipped})"
            )

        result_dataset = Dataset.from_list(processed_examples)
        logger.info(
            f"BiCodec preprocessing complete: {len(result_dataset)} examples "
            f"({skipped} skipped)\n"
        )
        # Debug: show first example text (truncated)
        sample = result_dataset[0]["text"]
        logger.info(f"Sample text (first 200 chars): {sample[:200]}...\n")
        logger.info(f"Sample text length: {len(sample)} chars\n")
        return result_dataset