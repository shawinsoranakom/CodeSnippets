def create_video(target_path: str, fps: float = 30.0) -> bool:
    """Create video with hardware-accelerated encoding and optimized settings."""
    temp_output_path = get_temp_output_path(target_path)
    temp_directory_path = get_temp_directory_path(target_path)

    # Determine optimal encoder based on available hardware
    encoder = modules.globals.video_encoder
    encoder_options = []

    # GPU-accelerated encoding options
    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        # NVIDIA GPU encoding
        if encoder == 'libx264':
            encoder = 'h264_nvenc'
            encoder_options = [
                "-preset", "p7",  # Highest quality preset for NVENC
                "-tune", "hq",  # High quality tuning
                "-rc", "vbr",  # Variable bitrate
                "-cq", str(modules.globals.video_quality),  # Quality level
                "-b:v", "0",  # Let CQ control bitrate
                "-multipass", "fullres",  # Two-pass encoding for better quality
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_nvenc'
            encoder_options = [
                "-preset", "p7",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", str(modules.globals.video_quality),
                "-b:v", "0",
            ]
    elif 'DmlExecutionProvider' in modules.globals.execution_providers:
        # AMD/Intel GPU encoding (DirectML on Windows)
        if encoder == 'libx264':
            # Try AMD AMF encoder
            encoder = 'h264_amf'
            encoder_options = [
                "-quality", "quality",  # Quality mode
                "-rc", "vbr_latency",
                "-qp_i", str(modules.globals.video_quality),
                "-qp_p", str(modules.globals.video_quality),
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_amf'
            encoder_options = [
                "-quality", "quality",
                "-rc", "vbr_latency",
                "-qp_i", str(modules.globals.video_quality),
                "-qp_p", str(modules.globals.video_quality),
            ]
    else:
        # CPU encoding with optimized settings
        if encoder == 'libx264':
            encoder_options = [
                "-preset", "medium",  # Balance speed/quality
                "-crf", str(modules.globals.video_quality),
                "-tune", "film",  # Optimize for film content
            ]
        elif encoder == 'libx265':
            encoder_options = [
                "-preset", "medium",
                "-crf", str(modules.globals.video_quality),
                "-x265-params", "log-level=error",
            ]
        elif encoder == 'libvpx-vp9':
            encoder_options = [
                "-crf", str(modules.globals.video_quality),
                "-b:v", "0",  # Constant quality mode
                "-cpu-used", "2",  # Speed vs quality (0-5, lower=slower/better)
            ]

    # Build ffmpeg command
    ffmpeg_args = [
        "-r", str(fps),
        "-i", os.path.join(temp_directory_path, "%04d.png"),
        "-c:v", encoder,
    ]

    # Add encoder-specific options
    ffmpeg_args.extend(encoder_options)

    # Add common options
    ffmpeg_args.extend([
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # Enable fast start for web playback
        "-vf", "colorspace=bt709:iall=bt601-6-625:fast=1",
        "-y",
        temp_output_path,
    ])

    # Try with hardware encoder first, fallback to software if it fails
    success = run_ffmpeg(ffmpeg_args)

    if not success and encoder in ['h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf']:
        # Fallback to software encoding
        print(f"Hardware encoding with {encoder} failed, falling back to software encoding...")
        fallback_encoder = 'libx264' if 'h264' in encoder else 'libx265'
        ffmpeg_args_fallback = [
            "-r", str(fps),
            "-i", os.path.join(temp_directory_path, "%04d.png"),
            "-c:v", fallback_encoder,
            "-preset", "medium",
            "-crf", str(modules.globals.video_quality),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-vf", "colorspace=bt709:iall=bt601-6-625:fast=1",
            "-y",
            temp_output_path,
        ]
        success = run_ffmpeg(ffmpeg_args_fallback)
    return success and os.path.isfile(temp_output_path)