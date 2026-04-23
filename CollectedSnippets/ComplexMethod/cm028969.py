async def test_start_stop_recording_produces_video(browser_session: BrowserSession, page_url: str, tmp_path: Path):
	"""start_recording → activity → stop_recording should write a valid MP4."""
	watchdog = browser_session._recording_watchdog
	assert watchdog is not None, 'BrowserSession should always attach a RecordingWatchdog'

	out_path = tmp_path / 'session.mp4'
	assert not watchdog.is_recording

	saved = await watchdog.start_recording(out_path)
	assert saved == out_path
	assert watchdog.is_recording

	await _drive_browser_briefly(browser_session, page_url)

	final = await watchdog.stop_recording()
	assert final == out_path
	assert not watchdog.is_recording
	assert out_path.exists(), 'recording stop should leave a file on disk'
	assert out_path.stat().st_size > 0, 'recorded video must be non-empty'

	# Confirm the file is actually a decodable video with at least one frame.
	reader: Any = iio.get_reader(str(out_path))
	try:
		frame: Any = reader.get_next_data()
		assert frame is not None and frame.size > 0
	finally:
		reader.close()