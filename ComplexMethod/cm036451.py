def test_opencv_video_io_colorspace(tmp_path, is_color: bool, fourcc: str, ext: str):
    """
    Test all functions that use OpenCV for video I/O return RGB format.
    Both RGB and grayscale videos are tested.
    """
    image_path = get_vllm_public_assets(
        filename="stop_sign.jpg", s3_prefix="vision_model_images"
    )
    image = Image.open(image_path)

    if not is_color:
        image_path = f"{tmp_path}/test_grayscale_image.png"
        image = image.convert("L")
        image.save(image_path)
        # Convert to gray RGB for comparison
        image = image.convert("RGB")
    video_path = f"{tmp_path}/test_RGB_video.{ext}"
    create_video_from_image(
        image_path,
        video_path,
        num_frames=2,
        is_color=is_color,
        fourcc=fourcc,
    )

    frames = video_to_ndarrays(video_path)
    for frame in frames:
        sim = cosine_similarity(
            normalize_image(np.array(frame)), normalize_image(np.array(image))
        )
        assert np.sum(np.isnan(sim)) / sim.size < 0.001
        assert np.nanmean(sim) > 0.99

    pil_frames = video_to_pil_images_list(video_path)
    for frame in pil_frames:
        sim = cosine_similarity(
            normalize_image(np.array(frame)), normalize_image(np.array(image))
        )
        assert np.sum(np.isnan(sim)) / sim.size < 0.001
        assert np.nanmean(sim) > 0.99

    io_frames, _ = VideoMediaIO(ImageMediaIO()).load_file(Path(video_path))
    for frame in io_frames:
        sim = cosine_similarity(
            normalize_image(np.array(frame)), normalize_image(np.array(image))
        )
        assert np.sum(np.isnan(sim)) / sim.size < 0.001
        assert np.nanmean(sim) > 0.99