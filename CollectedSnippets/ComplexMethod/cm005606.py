def preprocess(self, audio, candidate_labels=None, hypothesis_template="This is a sound of {}."):
        if isinstance(audio, str):
            if audio.startswith("http://") or audio.startswith("https://"):
                # We need to actually check for a real protocol, otherwise it's impossible to use a local file
                # like http_huggingface_co.png
                audio = httpx.get(audio, follow_redirects=True).content
            else:
                with open(audio, "rb") as f:
                    audio = f.read()

        if isinstance(audio, bytes):
            audio = ffmpeg_read(audio, self.feature_extractor.sampling_rate)

        if not isinstance(audio, np.ndarray):
            raise TypeError("We expect a numpy ndarray as input")
        if len(audio.shape) != 1:
            raise ValueError("We expect a single channel audio input for ZeroShotAudioClassificationPipeline")

        inputs = self.feature_extractor(
            [audio], sampling_rate=self.feature_extractor.sampling_rate, return_tensors="pt"
        )
        inputs = inputs.to(self.dtype)
        inputs["candidate_labels"] = candidate_labels
        sequences = [hypothesis_template.format(x) for x in candidate_labels]
        text_inputs = self.tokenizer(sequences, return_tensors="pt", padding=True)
        inputs["text_inputs"] = [text_inputs]
        return inputs