def test_solution(name, solution_class, needs_frame_count, video_key, kwargs_update, tmp_path, solution_assets):
    """Test individual Ultralytics solution with video processing and parameter validation."""
    # Get video path from persistent cache (no copying needed, read-only access)
    video_path = str(solution_assets(video_key)) if video_key else None

    # Update kwargs to use cached paths for parking manager
    kwargs = {}
    for key, value in kwargs_update.items():
        if key.startswith("temp_"):
            kwargs[key.replace("temp_", "")] = str(tmp_path / value)
        elif value == "parking_model":
            kwargs[key] = str(solution_assets("parking_model"))
        elif value == "parking_areas":
            kwargs[key] = str(solution_assets("parking_areas"))
        else:
            kwargs[key] = value

    if name == "StreamlitInference":
        if checks.check_imshow():  # do not merge with elif above
            solution_class(**kwargs).inference()  # requires interactive GUI environment
        return

    process_video(
        solution=solution_class(**kwargs),
        video_path=video_path,
        needs_frame_count=needs_frame_count,
    )