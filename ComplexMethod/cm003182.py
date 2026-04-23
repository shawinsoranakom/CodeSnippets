def forward(
        self,
        input_values: torch.FloatTensor,
        padding_mask: torch.BoolTensor | None = None,
        bandwidth: float | None = None,
        audio_codes: torch.LongTensor | None = None,
        audio_scales: torch.Tensor | None = None,
        return_dict: bool | None = None,
        last_frame_pad_length: int | None = 0,
    ) -> tuple[torch.Tensor, torch.Tensor] | EncodecOutput:
        r"""
        input_values (`torch.FloatTensor` of shape `(batch_size, channels, sequence_length)`, *optional*):
            Raw audio input converted to Float and padded to the appropriate length in order to be encoded using chunks
            of length self.chunk_length and a stride of `config.chunk_stride`.
        padding_mask (`torch.BoolTensor` of shape `(batch_size, channels, sequence_length)`, *optional*):
            Mask to avoid computing scaling factors on padding token indices (can we avoid computing conv on these+).
            Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            <Tip warning={true}>

            `padding_mask` should always be passed, unless the input was truncated or not padded. This is because in
            order to process tensors effectively, the input audio should be padded so that `input_length % stride =
            step` with `step = chunk_length-stride`. This ensures that all chunks are of the same shape

            </Tip>
        bandwidth (`float`, *optional*):
            The target bandwidth. Must be one of `config.target_bandwidths`. If `None`, uses the smallest possible
            bandwidth. bandwidth is represented as a thousandth of what it is, e.g. 6kbps bandwidth is represented as
            `bandwidth == 6.0`
        audio_codes (`torch.LongTensor`  of shape `(nb_frames, batch_size, nb_quantizers, frame_len)`, *optional*):
            Discrete code embeddings computed using `model.encode`.
        audio_scales (list of length `nb_frames` of `torch.Tensor` of shape `(batch_size, 1)`, *optional*):
            Scaling factor for each `audio_codes` input.
        return_dict (`bool`, *optional*):
            Whether to return outputs as a dict.
        last_frame_pad_length (`int`, *optional*):
            The length of the padding in the last frame, if any. This is used to ensure that the encoded frames can be
            outputted as a tensor. This value should be passed during decoding to ensure padding is removed from the
            encoded frames.

        Examples:

        ```python
        >>> from datasets import load_dataset
        >>> from transformers import AutoProcessor, EncodecModel

        >>> dataset = load_dataset("hf-internal-testing/ashraq-esc50-1-dog-example")
        >>> audio_sample = dataset["train"]["audio"][0]["array"]

        >>> model_id = "facebook/encodec_24khz"
        >>> model = EncodecModel.from_pretrained(model_id)
        >>> processor = AutoProcessor.from_pretrained(model_id)

        >>> inputs = processor(raw_audio=audio_sample, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> audio_codes = outputs.audio_codes
        >>> audio_values = outputs.audio_values
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if padding_mask is None:
            padding_mask = torch.ones_like(input_values).bool()
        else:
            # ensure that channel dimension is present
            padding_mask = padding_mask.view(padding_mask.shape[0], -1, padding_mask.shape[-1])

        if audio_codes is not None and audio_scales is None:
            raise ValueError("You specified `audio_codes` but did not specify the `audio_scales`")

        if audio_scales is not None and audio_codes is None:
            raise ValueError("You specified `audio_scales` but did not specify the `audio_codes`")

        if audio_scales is None and audio_codes is None:
            audio_codes, audio_scales, last_frame_pad_length = self.encode(
                input_values, padding_mask, bandwidth, False
            )

        audio_values = self.decode(
            audio_codes,
            audio_scales,
            padding_mask,
            return_dict=return_dict,
            last_frame_pad_length=last_frame_pad_length,
        )[0]
        if not return_dict:
            return (audio_codes, audio_values)

        return EncodecOutput(audio_codes=audio_codes, audio_values=audio_values)