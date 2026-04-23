def preprocess(self, inputs):
        if isinstance(inputs, str):
            if inputs.startswith("http://") or inputs.startswith("https://"):
                # We need to actually check for a real protocol, otherwise it's impossible to use a local file
                # like http_huggingface_co.png
                inputs = httpx.get(inputs, follow_redirects=True).content
            else:
                with open(inputs, "rb") as f:
                    inputs = f.read()

        if isinstance(inputs, bytes):
            inputs = ffmpeg_read(inputs, self.feature_extractor.sampling_rate)

        if is_torch_available():
            import torch

            if isinstance(inputs, torch.Tensor):
                inputs = inputs.cpu().numpy()

        if is_torchcodec_available():
            import torch
            import torchcodec

            if isinstance(inputs, torchcodec.decoders.AudioDecoder):
                _audio_samples = inputs.get_all_samples()
                _array = _audio_samples.data
                inputs = {"array": _array, "sampling_rate": _audio_samples.sample_rate}

        if isinstance(inputs, dict):
            inputs = inputs.copy()  # So we don't mutate the original dictionary outside the pipeline
            # Accepting `"array"` which is the key defined in `datasets` for
            # better integration
            if not ("sampling_rate" in inputs and ("raw" in inputs or "array" in inputs)):
                raise ValueError(
                    "When passing a dictionary to AudioClassificationPipeline, the dict needs to contain a "
                    '"raw" key containing the numpy array or torch tensor representing the audio and a "sampling_rate" key, '
                    "containing the sampling_rate associated with that array"
                )

            _inputs = inputs.pop("raw", None)
            if _inputs is None:
                # Remove path which will not be used from `datasets`.
                inputs.pop("path", None)
                _inputs = inputs.pop("array", None)
            in_sampling_rate = inputs.pop("sampling_rate")
            inputs = _inputs
            if in_sampling_rate != self.feature_extractor.sampling_rate:
                import torch

                if is_torchaudio_available():
                    from torchaudio import functional as F
                else:
                    raise ImportError(
                        "torchaudio is required to resample audio samples in AudioClassificationPipeline. "
                        "The torchaudio package can be installed through: `pip install torchaudio`."
                    )

                inputs = F.resample(
                    torch.from_numpy(inputs) if isinstance(inputs, np.ndarray) else inputs,
                    in_sampling_rate,
                    self.feature_extractor.sampling_rate,
                ).numpy()

        if not isinstance(inputs, np.ndarray):
            raise TypeError("We expect a numpy ndarray or torch tensor as input")
        if len(inputs.shape) != 1:
            raise ValueError("We expect a single channel audio input for AudioClassificationPipeline")

        processed = self.feature_extractor(
            inputs, sampling_rate=self.feature_extractor.sampling_rate, return_tensors="pt"
        )
        if self.dtype is not None:
            processed = processed.to(dtype=self.dtype)
        return processed