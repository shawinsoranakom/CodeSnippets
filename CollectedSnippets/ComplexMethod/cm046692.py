def process_split(ds, split_name = "train"):
            processed = []
            skipped = 0
            for idx in range(len(ds)):
                if self.should_stop:
                    logger.info(f"Stopped during Whisper {split_name} preprocessing\n")
                    break

                example = ds[idx]
                try:
                    audio_data = example.get(audio_col)
                    text = example.get(text_col)
                    if (
                        audio_data is None
                        or audio_data.get("array") is None
                        or not text
                    ):
                        skipped += 1
                        continue

                    # Extract audio features (notebook line 112-115)
                    features = self.tokenizer.feature_extractor(
                        audio_data["array"], sampling_rate = audio_data["sampling_rate"]
                    )
                    # Tokenize text (notebook line 116)
                    tokenized_text = self.tokenizer.tokenizer(text)

                    processed.append(
                        {
                            "input_features": features.input_features[0],
                            "labels": tokenized_text.input_ids,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Error processing Whisper {split_name} example {idx}: {e}"
                    )
                    skipped += 1
                    continue

                if (idx + 1) % 100 == 0:
                    self._update_progress(
                        status_message = f"Processing {split_name} audio... {idx + 1}/{len(ds)}"
                    )

            logger.info(
                f"Whisper {split_name} preprocessing: {len(processed)} examples ({skipped} skipped)\n"
            )
            return processed