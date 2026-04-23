def check_file_speeds(
    files: list[str], threshold_ms: float = 10, threshold_mb: float = 50, max_files: int = 5, prefix: str = ""
):
    """Check dataset file access speed and provide performance feedback.

    This function tests the access speed of dataset files by measuring ping (stat call) time and read speed. It samples
    up to `max_files` files from the provided list and warns if access times exceed the threshold.

    Args:
        files (list[str]): List of file paths to check for access speed.
        threshold_ms (float, optional): Threshold in milliseconds for ping time warnings.
        threshold_mb (float, optional): Threshold in megabytes per second for read speed warnings.
        max_files (int, optional): The maximum number of files to check.
        prefix (str, optional): Prefix string to add to log messages.

    Examples:
        >>> from pathlib import Path
        >>> image_files = list(Path("dataset/images").glob("*.jpg"))
        >>> check_file_speeds(image_files, threshold_ms=15)
    """
    if not files:
        LOGGER.warning(f"{prefix}Image speed checks: No files to check")
        return

    # Sample files (max 5)
    files = random.sample(files, min(max_files, len(files)))

    # Test ping (stat time)
    ping_times = []
    file_sizes = []
    read_speeds = []

    for f in files:
        try:
            # Measure ping (stat call)
            start = time.perf_counter()
            file_size = os.stat(f).st_size
            ping_times.append((time.perf_counter() - start) * 1000)  # ms
            file_sizes.append(file_size)

            # Measure read speed
            start = time.perf_counter()
            with open(f, "rb") as file_obj:
                _ = file_obj.read()
            read_time = time.perf_counter() - start
            if read_time > 0:  # Avoid division by zero
                read_speeds.append(file_size / (1 << 20) / read_time)  # MB/s
        except Exception:
            pass

    if not ping_times:
        LOGGER.warning(f"{prefix}Image speed checks: failed to access files")
        return

    # Calculate stats with uncertainties
    avg_ping = np.mean(ping_times)
    std_ping = np.std(ping_times, ddof=1) if len(ping_times) > 1 else 0
    size_msg = f", size: {np.mean(file_sizes) / (1 << 10):.1f} KB"
    ping_msg = f"ping: {avg_ping:.1f}±{std_ping:.1f} ms"

    if read_speeds:
        avg_speed = np.mean(read_speeds)
        std_speed = np.std(read_speeds, ddof=1) if len(read_speeds) > 1 else 0
        speed_msg = f", read: {avg_speed:.1f}±{std_speed:.1f} MB/s"
    else:
        speed_msg = ""

    if avg_ping < threshold_ms or avg_speed < threshold_mb:
        LOGGER.info(f"{prefix}Fast image access ✅ ({ping_msg}{speed_msg}{size_msg})")
    else:
        LOGGER.warning(
            f"{prefix}Slow image access detected ({ping_msg}{speed_msg}{size_msg}). "
            f"Use local storage instead of remote/mounted storage for better performance. "
            f"See https://docs.ultralytics.com/guides/model-training-tips/"
        )