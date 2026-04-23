def test_camera_sync(self, subtests):
    cam_states = ['roadCameraState', 'wideRoadCameraState', 'driverCameraState']
    encode_cams = ['roadEncodeIdx', 'wideRoadEncodeIdx', 'driverEncodeIdx']
    for cams in (cam_states, encode_cams):
      with subtests.test(cams=cams):
        # sanity checks within a single cam
        for cam in cams:
          with subtests.test(test="frame_skips", camera=cam):
            assert set(np.diff(self.ts[cam]['frameId'])) == {1, }, "Frame ID skips"

            # EOF > SOF
            eof_sof_diff = self.ts[cam]['timestampEof'] - self.ts[cam]['timestampSof']
            assert np.all(eof_sof_diff > 0)
            assert np.all(eof_sof_diff < 50*1e6)

        first_fid = {min(self.ts[c]['frameId']) for c in cams}
        assert len(first_fid) == 1, "Cameras don't start on same frame ID"
        if cam.endswith('CameraState'):
          # camerad guarantees that all cams start on frame ID 0
          # (note loggerd also needs to start up fast enough to catch it)
          assert next(iter(first_fid)) < 100, "Cameras start on frame ID too high"

        # we don't do a full segment rotation, so these might not match exactly
        last_fid = {max(self.ts[c]['frameId']) for c in cams}
        assert max(last_fid) - min(last_fid) < 10

        start, end = min(first_fid), min(last_fid)
        for i in range(end-start):
          # road and wide cameras (first two) should be synced within 2ms
          ts = {c: round(self.ts[c]['timestampSof'][i]/1e6, 1) for c in cams[:2]}
          diff = (max(ts.values()) - min(ts.values()))
          assert diff < 2, f"Cameras not synced properly: frame_id={start+i}, {diff=:.1f}ms, {ts=}"

          # driver camera should be staggered ~25ms from road camera
          offset_ms = abs(self.ts[cams[2]]['timestampSof'][i] - self.ts[cams[0]]['timestampSof'][i]) / 1e6
          assert 20 < offset_ms < 30, f"driver camera stagger out of range at frame {start+i}: {offset_ms:.1f}ms"