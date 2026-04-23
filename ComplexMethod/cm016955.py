def _build_asset_labels(
    reference_assets: dict[str, str],
    image_asset_uris: dict[str, str],
    video_asset_uris: dict[str, str],
    audio_asset_uris: dict[str, str],
    n_reference_images: int,
    n_reference_videos: int,
    n_reference_audios: int,
) -> dict[int, str]:
    """Map asset slot number (from 'asset_N' keys) to its positional label.

    Asset entries are appended to `content` after the reference_images/videos/audios,
    so their 1-indexed labels continue from the count of existing same-type refs:
    one reference_images entry + one Image-type asset -> asset labelled "Image 2".
    """
    image_n = n_reference_images
    video_n = n_reference_videos
    audio_n = n_reference_audios
    labels: dict[int, str] = {}
    for slot_key, raw_id in reference_assets.items():
        asset_id = (raw_id or "").strip()
        if not asset_id:
            continue
        try:
            slot_num = int(slot_key.rsplit("_", 1)[-1])
        except ValueError:
            continue
        if asset_id in image_asset_uris:
            image_n += 1
            labels[slot_num] = f"Image {image_n}"
        elif asset_id in video_asset_uris:
            video_n += 1
            labels[slot_num] = f"Video {video_n}"
        elif asset_id in audio_asset_uris:
            audio_n += 1
            labels[slot_num] = f"Audio {audio_n}"
    return labels