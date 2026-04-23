def draw_tracks_on_video(video, tracks, visibility=None, track_frame=24, circle_size=12, opacity=0.5, line_width=16):
    color_map = [(102, 153, 255), (0, 255, 255), (255, 255, 0), (255, 102, 204), (0, 255, 0)]

    video = video.byte().cpu().numpy()  # (81, 480, 832, 3)
    tracks = tracks[0].long().detach().cpu().numpy()
    if visibility is not None:
        visibility = visibility[0].detach().cpu().numpy()

    num_frames, height, width = video.shape[:3]
    num_tracks = tracks.shape[1]
    alpha_opacity = int(255 * opacity)

    output_frames = []
    for t in range(num_frames):
        frame_rgb = video[t].astype(np.float32)

        # Create a single RGBA overlay for all tracks in this frame
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        polyline_data = []

        # Draw all circles on a single overlay
        for n in range(num_tracks):
            if visibility is not None and visibility[t, n] == 0:
                continue

            track_coord = tracks[t, n]
            color = color_map[n % len(color_map)]
            circle_color = color + (alpha_opacity,)

            draw_overlay.ellipse((track_coord[0] - circle_size, track_coord[1] - circle_size, track_coord[0] + circle_size, track_coord[1] + circle_size),
                fill=circle_color
            )

            # Store polyline data for batch processing
            tracks_coord = tracks[max(t - track_frame, 0):t + 1, n]
            if len(tracks_coord) > 1:
                polyline_data.append((tracks_coord, color))

        # Blend circles overlay once
        overlay_np = np.array(overlay)
        alpha = overlay_np[:, :, 3:4] / 255.0
        frame_rgb = overlay_np[:, :, :3] * alpha + frame_rgb * (1 - alpha)

        # Draw all polylines on a single overlay
        if polyline_data:
            polyline_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            for tracks_coord, color in polyline_data:
                _draw_gradient_polyline_on_overlay(polyline_overlay, line_width, tracks_coord, color, opacity)

            # Blend polylines overlay once
            polyline_np = np.array(polyline_overlay)
            alpha = polyline_np[:, :, 3:4] / 255.0
            frame_rgb = polyline_np[:, :, :3] * alpha + frame_rgb * (1 - alpha)

        output_frames.append(Image.fromarray(frame_rgb.astype(np.uint8)))

    return output_frames