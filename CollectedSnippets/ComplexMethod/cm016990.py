def audio_bytes_to_audio_input(audio_bytes: bytes) -> dict:
    """
    Decode any common audio container from bytes using PyAV and return
    a Comfy AUDIO dict: {"waveform": [1, C, T] float32, "sample_rate": int}.
    """
    with av.open(BytesIO(audio_bytes)) as af:
        if not af.streams.audio:
            raise ValueError("No audio stream found in response.")
        stream = af.streams.audio[0]

        in_sr = int(stream.codec_context.sample_rate)
        out_sr = in_sr

        frames: list[torch.Tensor] = []
        n_channels = stream.channels or 1

        for frame in af.decode(streams=stream.index):
            arr = frame.to_ndarray()  # shape can be [C, T] or [T, C] or [T]
            buf = torch.from_numpy(arr)
            if buf.ndim == 1:
                buf = buf.unsqueeze(0)  # [T] -> [1, T]
            elif buf.shape[0] != n_channels and buf.shape[-1] == n_channels:
                buf = buf.transpose(0, 1).contiguous()  # [T, C] -> [C, T]
            elif buf.shape[0] != n_channels:
                buf = buf.reshape(-1, n_channels).t().contiguous()  # fallback to [C, T]
            frames.append(buf)

    if not frames:
        raise ValueError("Decoded zero audio frames.")

    wav = torch.cat(frames, dim=1)  # [C, T]
    wav = _f32_pcm(wav)
    return {"waveform": wav.unsqueeze(0).contiguous(), "sample_rate": out_sr}