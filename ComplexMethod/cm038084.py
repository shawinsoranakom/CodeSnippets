def merge_interleaved_embeddings(
    inputs_embeds: torch.Tensor,
    multimodal_embeddings: "MultiModalEmbeddings",
    is_video: torch.Tensor,
    is_audio: torch.Tensor,
    is_multimodal: torch.Tensor,
    num_video: int,
    num_audio: int,
) -> torch.Tensor:
    """
    Merge embeddings for interleaved audio-in-video sequences.

    When use_audio_in_video=True, video and audio tokens are interleaved in
    the token sequence, but embeddings are provided as separate contiguous
    tensors (video first, then audio). This function reorders video and audio
    embeddings to match sequence position order and scatters them efficiently.

    Args:
        inputs_embeds: The input embeddings tensor to merge into.
        multimodal_embeddings: List of embedding tensors (video, audio, other).
        is_video: Boolean mask for video token positions.
        is_audio: Boolean mask for audio token positions.
        is_multimodal: Boolean mask for all multimodal token positions.
        num_video: Total count of video tokens.
        num_audio: Total count of audio tokens.

    Returns:
        The merged inputs_embeds tensor with multimodal embeddings scattered
        to their correct positions.
    """
    # Categorize embeddings by modality based on token counts.
    # Embeddings come grouped by modality but order varies (e.g., image, video, audio
    # or video, audio depending on input kwargs order).
    video_embeds: list[torch.Tensor] = []
    audio_embeds: list[torch.Tensor] = []
    other_embeds: list[torch.Tensor] = []
    video_remaining = num_video
    audio_remaining = num_audio

    for emb in multimodal_embeddings:
        n = emb.shape[0]
        if video_remaining > 0 and n <= video_remaining:
            video_embeds.append(emb)
            video_remaining -= n
        elif audio_remaining > 0 and n <= audio_remaining:
            audio_embeds.append(emb)
            audio_remaining -= n
        else:
            other_embeds.append(emb)

    # Scatter each modality to its positions
    if video_embeds:
        inputs_embeds[is_video] = torch.cat(video_embeds, dim=0)
    if audio_embeds:
        inputs_embeds[is_audio] = torch.cat(audio_embeds, dim=0)
    if other_embeds:
        other_mask = is_multimodal & ~is_video & ~is_audio
        inputs_embeds[other_mask] = torch.cat(other_embeds, dim=0)

    return inputs_embeds