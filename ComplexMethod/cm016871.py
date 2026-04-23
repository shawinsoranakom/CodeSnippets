def execute(cls, width, height, start_x, start_y, mid_x, mid_y, end_x, end_y, num_frames, num_tracks,
                track_spread, bezier=False, interpolation="linear", track_mask=None) -> io.NodeOutput:
        device = comfy.model_management.intermediate_device()
        track_length = num_frames

        # normalized coordinates to pixel coordinates
        start_x_px = start_x * width
        start_y_px = start_y * height
        mid_x_px = mid_x * width
        mid_y_px = mid_y * height
        end_x_px = end_x * width
        end_y_px = end_y * height

        track_spread_px = track_spread * (width + height) / 2 # Use average of width/height for spread to keep it proportional

        t = torch.linspace(0, 1, num_frames, device=device)
        if interpolation == "constant": # All points stay at start position
            interp_values = torch.zeros_like(t)
        elif interpolation == "linear":
            interp_values = t
        elif interpolation == "ease_in":
            interp_values = t ** 2
        elif interpolation == "ease_out":
            interp_values = 1 - (1 - t) ** 2
        elif interpolation == "ease_in_out":
            interp_values = t * t * (3 - 2 * t)

        if bezier: # apply interpolation to t for timing control along the bezier path
            t_interp = interp_values
            one_minus_t = 1 - t_interp
            x_positions = one_minus_t ** 2 * start_x_px + 2 * one_minus_t * t_interp * mid_x_px + t_interp ** 2 * end_x_px
            y_positions = one_minus_t ** 2 * start_y_px + 2 * one_minus_t * t_interp * mid_y_px + t_interp ** 2 * end_y_px
            tangent_x = 2 * one_minus_t * (mid_x_px - start_x_px) + 2 * t_interp * (end_x_px - mid_x_px)
            tangent_y = 2 * one_minus_t * (mid_y_px - start_y_px) + 2 * t_interp * (end_y_px - mid_y_px)
        else: # calculate base x and y positions for each frame (center track)
            x_positions = start_x_px + (end_x_px - start_x_px) * interp_values
            y_positions = start_y_px + (end_y_px - start_y_px) * interp_values
            # For non-bezier, tangent is constant (direction from start to end)
            tangent_x = torch.full_like(t, end_x_px - start_x_px)
            tangent_y = torch.full_like(t, end_y_px - start_y_px)

        track_list = []
        for frame_idx in range(num_frames):
            # Calculate perpendicular direction at this frame
            tx = tangent_x[frame_idx].item()
            ty = tangent_y[frame_idx].item()
            length = (tx ** 2 + ty ** 2) ** 0.5

            if length > 0: # Perpendicular unit vector (rotate 90 degrees)
                perp_x = -ty / length
                perp_y = tx / length
            else: # If tangent is zero, spread horizontally
                perp_x = 1.0
                perp_y = 0.0

            frame_tracks = []
            for track_idx in range(num_tracks): # center tracks around the main path offset ranges from -(num_tracks-1)/2 to +(num_tracks-1)/2
                offset = (track_idx - (num_tracks - 1) / 2) * track_spread_px
                track_x = x_positions[frame_idx].item() + perp_x * offset
                track_y = y_positions[frame_idx].item() + perp_y * offset
                frame_tracks.append([track_x, track_y])
            track_list.append(frame_tracks)

        tracks = torch.tensor(track_list, dtype=torch.float32, device=device)  # [frames, num_tracks, 2]

        if track_mask is None:
            track_visibility = torch.ones((track_length, num_tracks), dtype=torch.bool, device=device)
        else:
            track_visibility = (track_mask > 0).any(dim=(1, 2)).unsqueeze(-1)

        out_track_info = {}
        out_track_info["track_path"] = tracks
        out_track_info["track_visibility"] = track_visibility
        return io.NodeOutput(out_track_info, track_length)