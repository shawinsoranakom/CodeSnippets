def run_pipeline_test(self, speech_recognizer, examples):
        audio = np.zeros((34000,))
        outputs = speech_recognizer(audio)
        self.assertEqual(outputs, {"text": ANY(str)})

        compare_pipeline_output_to_hub_spec(outputs, AutomaticSpeechRecognitionOutput)

        # Striding
        audio = {"raw": audio, "stride": (0, 4000), "sampling_rate": speech_recognizer.feature_extractor.sampling_rate}
        if speech_recognizer.type == "ctc":
            outputs = speech_recognizer(audio)
            self.assertEqual(outputs, {"text": ANY(str)})
        elif "Whisper" in speech_recognizer.model.__class__.__name__:
            outputs = speech_recognizer(audio)
            self.assertEqual(outputs, {"text": ANY(str)})
        else:
            # Non CTC models cannot use striding.
            with self.assertRaises(ValueError):
                outputs = speech_recognizer(audio)

        # Timestamps
        audio = np.zeros((34000,))
        if speech_recognizer.type == "ctc":
            outputs = speech_recognizer(audio, return_timestamps="char")
            self.assertIsInstance(outputs["chunks"], list)
            n = len(outputs["chunks"])
            self.assertEqual(
                outputs,
                {
                    "text": ANY(str),
                    "chunks": [{"text": ANY(str), "timestamp": (ANY(float), ANY(float))} for i in range(n)],
                },
            )

            outputs = speech_recognizer(audio, return_timestamps="word")
            self.assertIsInstance(outputs["chunks"], list)
            n = len(outputs["chunks"])
            self.assertEqual(
                outputs,
                {
                    "text": ANY(str),
                    "chunks": [{"text": ANY(str), "timestamp": (ANY(float), ANY(float))} for i in range(n)],
                },
            )
        elif "Whisper" in speech_recognizer.model.__class__.__name__:
            outputs = speech_recognizer(audio, return_timestamps=True)
            self.assertIsInstance(outputs["chunks"], list)
            nb_chunks = len(outputs["chunks"])
            self.assertGreater(nb_chunks, 0)
            self.assertEqual(
                outputs,
                {
                    "text": ANY(str),
                    "chunks": [{"text": ANY(str), "timestamp": (ANY(float), ANY(float))} for i in range(nb_chunks)],
                },
            )
        else:
            # Non CTC models cannot use return_timestamps
            with self.assertRaisesRegex(
                ValueError, "^We cannot return_timestamps yet on non-CTC models apart from Whisper!$"
            ):
                outputs = speech_recognizer(audio, return_timestamps="char")