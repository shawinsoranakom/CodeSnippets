def get_audio_embed_bucket_fps(audio_embed, fps=16, batch_frames=81, m=0, video_rate=30):
    num_layers, audio_frame_num, audio_dim = audio_embed.shape

    if num_layers > 1:
        return_all_layers = True
    else:
        return_all_layers = False

    scale = video_rate / fps

    min_batch_num = int(audio_frame_num / (batch_frames * scale)) + 1

    bucket_num = min_batch_num * batch_frames
    padd_audio_num = math.ceil(min_batch_num * batch_frames / fps * video_rate) - audio_frame_num
    batch_idx = get_sample_indices(
        original_fps=video_rate,
        total_frames=audio_frame_num + padd_audio_num,
        target_fps=fps,
        num_sample=bucket_num,
        fixed_start=0)
    batch_audio_eb = []
    audio_sample_stride = int(video_rate / fps)
    for bi in batch_idx:
        if bi < audio_frame_num:

            chosen_idx = list(
                range(bi - m * audio_sample_stride, bi + (m + 1) * audio_sample_stride, audio_sample_stride))
            chosen_idx = [0 if c < 0 else c for c in chosen_idx]
            chosen_idx = [
                audio_frame_num - 1 if c >= audio_frame_num else c
                for c in chosen_idx
            ]

            if return_all_layers:
                frame_audio_embed = audio_embed[:, chosen_idx].flatten(
                    start_dim=-2, end_dim=-1)
            else:
                frame_audio_embed = audio_embed[0][chosen_idx].flatten()
        else:
            frame_audio_embed = torch.zeros([audio_dim * (2 * m + 1)], device=audio_embed.device) if not return_all_layers \
                else torch.zeros([num_layers, audio_dim * (2 * m + 1)], device=audio_embed.device)
        batch_audio_eb.append(frame_audio_embed)
    batch_audio_eb = torch.cat([c.unsqueeze(0) for c in batch_audio_eb], dim=0)

    return batch_audio_eb, min_batch_num