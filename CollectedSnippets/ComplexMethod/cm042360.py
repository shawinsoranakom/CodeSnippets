def test_frame_sync(self, logs):
    SYNCED_CAMS = ('roadCameraState', 'wideRoadCameraState')
    n = range(len(logs['roadCameraState']['t'][:-10]))

    frame_ids = {i: [logs[cam]['frameId'][i] for cam in CAMERAS] for i in n}
    assert all(len(set(v)) == 1 for v in frame_ids.values()), "frame IDs not aligned"

    # road and wide cameras should be synced within 1.1ms
    synced_times = {i: [logs[cam]['timestampSof'][i] for cam in SYNCED_CAMS] for i in n}
    diffs = {i: (max(ts) - min(ts))/1e6 for i, ts in synced_times.items()}
    laggy_frames = {k: v for k, v in diffs.items() if v > 1.1}
    assert len(laggy_frames) == 0, f"Frames not synced properly: {laggy_frames=}"

    # driver camera should be staggered ~25ms from road camera
    for i in n:
      offset_ms = abs(logs['driverCameraState']['timestampSof'][i] - logs['roadCameraState']['timestampSof'][i]) / 1e6
      assert 20 < offset_ms < 30, f"driver camera stagger out of range at frame {i}: {offset_ms:.1f}ms (expected ~25ms)"