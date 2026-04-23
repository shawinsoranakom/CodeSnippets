def make_batched_metadata(videos: VideoInput, video_metadata: VideoMetadataType) -> list[VideoMetadata]:
    if video_metadata is None:
        # Create default metadata and fill attributes we can infer from given video
        video_metadata = [
            {
                "total_num_frames": len(video),
                "fps": None,
                "duration": None,
                "frames_indices": list(range(len(video))),
                "height": get_video_size(video)[0] if is_valid_video(video) else None,
                "width": get_video_size(video)[1] if is_valid_video(video) else None,
            }
            for video in videos
        ]

    if isinstance(video_metadata, list):
        # Flatten if nested list
        if isinstance(video_metadata[0], list):
            video_metadata = [
                VideoMetadata(**metadata) for metadata_list in video_metadata for metadata in metadata_list
            ]
        # Simply wrap in VideoMetadata if simple dict
        elif isinstance(video_metadata[0], dict):
            video_metadata = [VideoMetadata(**metadata) for metadata in video_metadata]
    else:
        # Create a batched list from single object
        video_metadata = [VideoMetadata(**video_metadata)]
    return video_metadata