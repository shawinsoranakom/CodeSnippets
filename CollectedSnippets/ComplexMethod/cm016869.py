def create_pos_embeddings(
    pred_tracks: torch.Tensor, # the predicted tracks, [T, N, 2]
    pred_visibility: torch.Tensor, # the predicted visibility [T, N]
    downsample_ratios: list[int], # the ratios for downsampling time, height, and width
    height: int, # the height of the feature map
    width: int, # the width of the feature map
    track_num: int = -1, # the number of tracks to use
    t_down_strategy: str = "sample", # the strategy for downsampling time dimension
):
    assert t_down_strategy in ["sample", "average"], "Invalid strategy for downsampling time dimension."

    t, n, _ = pred_tracks.shape
    t_down, h_down, w_down = downsample_ratios
    track_pos = - torch.ones(n, (t-1) // t_down + 1, 2, dtype=torch.long)

    if track_num == -1:
        track_num = n

    tracks_idx = torch.randperm(n)[:track_num]
    tracks = pred_tracks[:, tracks_idx]
    visibility = pred_visibility[:, tracks_idx]

    for t_idx in range(0, t, t_down):
        if t_down_strategy == "sample" or t_idx == 0:
            cur_tracks = tracks[t_idx] # [N, 2]
            cur_visibility = visibility[t_idx] # [N]
        else:
            cur_tracks = tracks[t_idx:t_idx+t_down].mean(dim=0)
            cur_visibility = torch.any(visibility[t_idx:t_idx+t_down], dim=0)

        for i in range(track_num):
            if not cur_visibility[i] or cur_tracks[i][0] < 0 or cur_tracks[i][1] < 0 or cur_tracks[i][0] >= width or cur_tracks[i][1] >= height:
                continue
            x, y = cur_tracks[i]
            x, y = int(x // w_down), int(y // h_down)
            track_pos[i, t_idx // t_down, 0], track_pos[i, t_idx // t_down, 1] = y, x

    return track_pos