def normalize_audio(
    audio: npt.NDArray[np.floating] | torch.Tensor,
    spec: AudioSpec,
) -> npt.NDArray[np.floating] | torch.Tensor:
    """Normalize audio to the specified format.

    This function handles channel reduction for multi-channel audio,
    supporting both numpy arrays and torch tensors.

    Args:
        audio: Input audio data. Can be:
            - 1D array/tensor: (time,) - already mono
            - 2D array/tensor: (channels, time) - standard format from torchaudio
            - 2D array/tensor: (time, channels) - format from soundfile
              (will be auto-detected and transposed if time > channels)
        spec: AudioSpec defining the target format.

    Returns:
        Normalized audio in the same type as input (numpy or torch).
        For mono output (target_channels=1), returns 1D array/tensor.

    Raises:
        ValueError: If audio has unsupported dimensions or channel expansion
            is requested (e.g., mono to stereo).
    """
    if not spec.needs_normalization:
        return audio

    # Handle 1D audio (already mono)
    if audio.ndim == 1:
        if spec.target_channels == 1:
            return audio
        raise ValueError(f"Cannot expand mono audio to {spec.target_channels} channels")

    # Handle 2D audio
    if audio.ndim != 2:
        raise ValueError(f"Unsupported audio shape: {audio.shape}. Expected 1D or 2D.")

    # Auto-detect format: if shape[0] > shape[1], assume (time, channels)
    # This handles soundfile format where time dimension is typically much larger
    if audio.shape[0] > audio.shape[1]:
        # Transpose from (time, channels) to (channels, time)
        audio = audio.T if isinstance(audio, np.ndarray) else audio.T

    num_channels = audio.shape[0]

    # No reduction needed if already at target
    if num_channels == spec.target_channels:
        return audio

    # Cannot expand channels
    if num_channels < spec.target_channels:
        raise ValueError(
            f"Cannot expand {num_channels} channels to {spec.target_channels}"
        )

    # Reduce channels
    is_numpy = isinstance(audio, np.ndarray)

    if spec.target_channels == 1:
        # Reduce to mono
        if spec.channel_reduction == ChannelReduction.MEAN:
            result = np.mean(audio, axis=0) if is_numpy else audio.mean(dim=0)
        elif spec.channel_reduction == ChannelReduction.FIRST:
            result = audio[0]
        elif spec.channel_reduction == ChannelReduction.MAX:
            result = np.max(audio, axis=0) if is_numpy else audio.max(dim=0).values
        elif spec.channel_reduction == ChannelReduction.SUM:
            result = np.sum(audio, axis=0) if is_numpy else audio.sum(dim=0)
        else:
            raise ValueError(f"Unknown reduction method: {spec.channel_reduction}")
        return result
    else:
        # Reduce to N channels (take first N and apply reduction if needed)
        # For now, just take first N channels
        return audio[: spec.target_channels]