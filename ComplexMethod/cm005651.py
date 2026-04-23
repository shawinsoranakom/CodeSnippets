def preprocess(self, inputs, chunk_length_s=0, stride_length_s=None):
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

        stride = None
        extra = {}

        if is_torch_available():
            import torch

            if isinstance(inputs, torch.Tensor):
                inputs = inputs.cpu().numpy()

        if is_torchcodec_available():
            import torchcodec

            if isinstance(inputs, torchcodec.decoders.AudioDecoder):
                _audio_samples = inputs.get_all_samples()

                # torchcodec always returns (num_channels, num_samples)
                # while before (datasets < 4.0) we had (2, num_samples) if stereo, (num_samples,) if mono
                _array = _audio_samples.data
                _array = _array[0] if _array.ndim == 2 and _array.shape[0] == 1 else _array
                inputs = {"array": _array, "sampling_rate": _audio_samples.sample_rate}

        if isinstance(inputs, dict):
            stride = inputs.pop("stride", None)
            # Accepting `"array"` which is the key defined in `datasets` for
            # better integration
            if not ("sampling_rate" in inputs and ("raw" in inputs or "array" in inputs)):
                raise ValueError(
                    "When passing a dictionary to AutomaticSpeechRecognitionPipeline, the dict needs to contain a "
                    '"raw" key containing the numpy array or torch tensor representing the audio and a "sampling_rate" key, '
                    "containing the sampling_rate associated with that array"
                )

            _inputs = inputs.pop("raw", None)
            if _inputs is None:
                # Remove path which will not be used from `datasets`.
                inputs.pop("path", None)
                _inputs = inputs.pop("array", None)
            in_sampling_rate = inputs.pop("sampling_rate")
            extra = inputs
            inputs = _inputs
            if in_sampling_rate != self.feature_extractor.sampling_rate:
                if is_torchaudio_available():
                    from torchaudio import functional as F
                else:
                    raise ImportError(
                        "torchaudio is required to resample audio samples in AutomaticSpeechRecognitionPipeline. "
                        "The torchaudio package can be installed through: `pip install torchaudio`."
                    )

                inputs = F.resample(
                    torch.from_numpy(inputs) if isinstance(inputs, np.ndarray) else inputs,
                    in_sampling_rate,
                    self.feature_extractor.sampling_rate,
                ).numpy()
                ratio = self.feature_extractor.sampling_rate / in_sampling_rate
            else:
                ratio = 1
            if stride is not None:
                if stride[0] + stride[1] > inputs.shape[0]:
                    raise ValueError("Stride is too large for input")

                # Stride needs to get the chunk length here, it's going to get
                # swallowed by the `feature_extractor` later, and then batching
                # can add extra data in the inputs, so we need to keep track
                # of the original length in the stride so we can cut properly.
                stride = (inputs.shape[0], int(round(stride[0] * ratio)), int(round(stride[1] * ratio)))
        if not isinstance(inputs, (np.ndarray, torch.Tensor)):
            raise TypeError(f"We expect a numpy ndarray or torch tensor as input, got `{type(inputs)}`")
        if inputs.ndim != 1:
            logger.warning(
                f"We expect a single channel audio input for AutomaticSpeechRecognitionPipeline, got {inputs.ndim}. Taking the mean of the channels for mono conversion."
            )
            inputs = inputs.mean(axis=0)

        if chunk_length_s:
            if stride_length_s is None:
                stride_length_s = chunk_length_s / 6

            if isinstance(stride_length_s, (int, float)):
                stride_length_s = [stride_length_s, stride_length_s]

            align_to = self._align_to
            chunk_len = int(round(chunk_length_s * self.feature_extractor.sampling_rate / align_to) * align_to)
            stride_left = int(round(stride_length_s[0] * self.feature_extractor.sampling_rate / align_to) * align_to)
            stride_right = int(round(stride_length_s[1] * self.feature_extractor.sampling_rate / align_to) * align_to)

            if chunk_len < stride_left + stride_right:
                raise ValueError("Chunk length must be superior to stride length")

            for item in chunk_iter(inputs, self.feature_extractor, chunk_len, stride_left, stride_right, self.dtype):
                yield {**item, **extra}
        else:
            if self.type == "seq2seq_whisper" and inputs.shape[0] > self.feature_extractor.n_samples:
                processed = self.feature_extractor(
                    inputs,
                    sampling_rate=self.feature_extractor.sampling_rate,
                    truncation=False,
                    padding="longest",
                    return_tensors="pt",
                    return_attention_mask=True,
                )
            else:
                if self.type == "seq2seq_whisper" and stride is None:
                    processed = self.feature_extractor(
                        inputs,
                        sampling_rate=self.feature_extractor.sampling_rate,
                        return_tensors="pt",
                        return_attention_mask=True,
                    )
                else:
                    processed = self.feature_extractor(
                        inputs,
                        sampling_rate=self.feature_extractor.sampling_rate,
                        return_tensors="pt",
                        return_attention_mask=True,
                    )
            if self.dtype is not None:
                processed = processed.to(dtype=self.dtype)
            if stride is not None:
                if self.type == "seq2seq":
                    raise ValueError("Stride is only usable with CTC models, try removing it !")

                processed["stride"] = stride
            yield {"is_last": True, **processed, **extra}