def _preprocess_dac_dataset(self, dataset, custom_format_mapping = None):
        """Preprocess dataset for OuteTTS training with DAC codec.

        Mirrors Oute_TTS_(1B).ipynb DataCreationV3: uses Whisper for word timings,
        OuteTTS AudioProcessor for speaker representations, PromptProcessor for
        training prompts. Outputs text strings for SFTTrainer with dataset_text_field="text".
        """
        import sys
        import io
        import tempfile
        import torch
        import numpy as np
        import soundfile as sf
        from datasets import Dataset as HFDataset
        from utils.paths import ensure_dir, tmp_root

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Clone OuteTTS repo (same as audio_codecs._load_dac)
        import subprocess

        base_dir = os.path.dirname(os.path.abspath(__file__))
        outetts_code_dir = os.path.join(base_dir, "inference", "OuteTTS")
        outetts_pkg = os.path.join(outetts_code_dir, "outetts")
        if not os.path.isdir(outetts_pkg):
            self._update_progress(status_message = "Cloning OuteTTS code repo...")
            logger.info(f"Cloning edwko/OuteTTS to {outetts_code_dir}...\n")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/edwko/OuteTTS",
                    outetts_code_dir,
                ],
                check = True,
            )
            for fpath in [
                os.path.join(outetts_pkg, "models", "gguf_model.py"),
                os.path.join(outetts_pkg, "interface.py"),
                os.path.join(outetts_pkg, "__init__.py"),
            ]:
                if os.path.exists(fpath):
                    os.remove(fpath)
                    logger.info(f"Removed {fpath}\n")

        if outetts_code_dir not in sys.path:
            sys.path.insert(0, outetts_code_dir)

        from outetts.version.v3.audio_processor import AudioProcessor
        from outetts.version.v3.prompt_processor import PromptProcessor
        from outetts.models.config import ModelConfig as OuteTTSModelConfig
        from outetts.utils.preprocessing import text_normalizations

        # Resolve audio and text columns
        resolved = self._resolve_audio_columns(dataset, custom_format_mapping)
        audio_col = resolved["audio_col"]
        text_col = resolved["text_col"]
        if not audio_col or not text_col:
            raise ValueError(
                f"DAC dataset needs 'audio' and 'text' columns, got: {dataset.column_names}"
            )

        # Cast audio to 24kHz (notebook: dataset.cast_column("audio", Audio(sampling_rate=24000)))
        from datasets import Audio

        dataset = dataset.cast_column(audio_col, Audio(sampling_rate = 24000))
        logger.info("Cast audio column to 24kHz\n")

        # Load Whisper for word timings
        self._update_progress(
            status_message = "Loading Whisper model for word timings..."
        )
        logger.info("Loading Whisper model for word timings...\n")
        import whisper

        whisper_model = whisper.load_model("turbo", device = device)

        # Load OuteTTS AudioProcessor + PromptProcessor
        self._update_progress(status_message = "Loading OuteTTS AudioProcessor...")
        logger.info("Loading OuteTTS AudioProcessor...\n")
        model_tokenizer_path = "OuteAI/Llama-OuteTTS-1.0-1B"
        dummy_config = OuteTTSModelConfig(
            tokenizer_path = model_tokenizer_path,
            device = device,
            audio_codec_path = None,
        )
        audio_processor = AudioProcessor(config = dummy_config)
        prompt_processor = PromptProcessor(model_tokenizer_path)

        self._update_progress(status_message = "Preprocessing audio with OuteTTS...")
        logger.info(
            f"DAC preprocessing: audio_col='{audio_col}', text_col='{text_col}'\n"
        )

        processed_examples = []
        skipped = 0
        for idx in range(len(dataset)):
            if self.should_stop:
                logger.info("Stopped during DAC preprocessing\n")
                break

            example = dataset[idx]
            try:
                text = example.get(text_col)
                if not text or not isinstance(text, str):
                    skipped += 1
                    continue

                audio_data = example.get(audio_col)
                if audio_data is None or audio_data.get("array") is None:
                    skipped += 1
                    continue

                audio_array = np.array(audio_data["array"], dtype = np.float32)
                sampling_rate = audio_data.get("sampling_rate", 24000)

                # Convert to WAV bytes (Whisper needs a file path)
                buf = io.BytesIO()
                sf.write(buf, audio_array, sampling_rate, format = "WAV", subtype = "FLOAT")
                buf.seek(0)
                audio_bytes = buf.getvalue()

                # 1. Get word timings from Whisper
                with tempfile.NamedTemporaryFile(
                    suffix = ".wav",
                    delete = False,
                    dir = str(ensure_dir(tmp_root())),
                ) as tmp:
                    tmp.write(audio_bytes)
                    tmp.flush()
                    tmp_path = tmp.name
                try:
                    whisper_result = whisper_model.transcribe(
                        tmp_path, word_timestamps = True
                    )
                finally:
                    Path(tmp_path).unlink(missing_ok = True)

                normalized_transcript = text_normalizations(text)
                words_with_timings = []
                if whisper_result and "segments" in whisper_result:
                    for segment in whisper_result["segments"]:
                        for word_info in segment.get("words", []):
                            cleaned = word_info["word"].strip()
                            if cleaned:
                                words_with_timings.append(
                                    {
                                        "word": cleaned,
                                        "start": float(word_info["start"]),
                                        "end": float(word_info["end"]),
                                    }
                                )

                if not words_with_timings:
                    skipped += 1
                    continue

                # 2. Create speaker representation with AudioProcessor
                speaker_data_dict = {
                    "audio": {"bytes": audio_bytes},
                    "text": normalized_transcript,
                    "words": words_with_timings,
                }
                speaker = audio_processor.create_speaker_from_dict(speaker_data_dict)
                if speaker is None:
                    skipped += 1
                    continue

                # 3. Get training prompt from PromptProcessor
                prompt = prompt_processor.get_training_prompt(speaker)
                if prompt:
                    processed_examples.append({"text": prompt})

            except Exception as e:
                logger.warning(f"Error processing DAC example {idx}: {e}")
                skipped += 1
                continue

            if (idx + 1) % 100 == 0:
                self._update_progress(
                    status_message = f"Preprocessing audio with OuteTTS... {idx + 1}/{len(dataset)}"
                )

        # Free Whisper from GPU (notebook: data_processor.whisper_model.to('cpu'))
        logger.info("Moving Whisper model to CPU...\n")
        whisper_model.to("cpu")
        del whisper_model
        del audio_processor
        del prompt_processor
        import gc

        gc.collect()
        torch.cuda.empty_cache()
        self._cuda_audio_used = True

        if not processed_examples:
            raise ValueError(
                f"No valid examples after DAC preprocessing (skipped {skipped})"
            )

        result_dataset = HFDataset.from_list(processed_examples)
        logger.info(
            f"DAC preprocessing complete: {len(result_dataset)} examples "
            f"({skipped} skipped)\n"
        )
        sample = result_dataset[0]["text"]
        logger.info(f"Sample text (first 200 chars): {sample[:200]}...\n")
        return result_dataset