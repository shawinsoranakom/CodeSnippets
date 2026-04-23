def test_processor_batch_decode(self):
        feature_extractor = self.get_feature_extractor()
        tokenizer = self.get_tokenizer()

        processor = Pop2PianoProcessor(
            tokenizer=tokenizer,
            feature_extractor=feature_extractor,
        )

        audio, sampling_rate, token_ids, _ = self.get_inputs()
        feature_extractor_output = feature_extractor(audio=audio, sampling_rate=sampling_rate, return_tensors="pt")

        encoded_processor = processor.batch_decode(
            token_ids=token_ids,
            feature_extractor_output=feature_extractor_output,
            return_midi=True,
        )

        encoded_tokenizer = tokenizer.batch_decode(
            token_ids=token_ids,
            feature_extractor_output=feature_extractor_output,
            return_midi=True,
        )
        # check start timings
        encoded_processor_start_timings = [token.start for token in encoded_processor["notes"]]
        encoded_tokenizer_start_timings = [token.start for token in encoded_tokenizer["notes"]]
        self.assertListEqual(encoded_processor_start_timings, encoded_tokenizer_start_timings)

        # check end timings
        encoded_processor_end_timings = [token.end for token in encoded_processor["notes"]]
        encoded_tokenizer_end_timings = [token.end for token in encoded_tokenizer["notes"]]
        self.assertListEqual(encoded_processor_end_timings, encoded_tokenizer_end_timings)

        # check pitch
        encoded_processor_pitch = [token.pitch for token in encoded_processor["notes"]]
        encoded_tokenizer_pitch = [token.pitch for token in encoded_tokenizer["notes"]]
        self.assertListEqual(encoded_processor_pitch, encoded_tokenizer_pitch)

        # check velocity
        encoded_processor_velocity = [token.velocity for token in encoded_processor["notes"]]
        encoded_tokenizer_velocity = [token.velocity for token in encoded_tokenizer["notes"]]
        self.assertListEqual(encoded_processor_velocity, encoded_tokenizer_velocity)