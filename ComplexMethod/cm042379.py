def check_seg(i):
      # check each camera file size
      counts = []
      first_frames = []
      for camera, fps, size_lambda, encode_idx_name in CAMERAS:
        if not record_front and "dcamera" in camera:
          continue

        file_path = f"{route_prefix_path}--{i}/{camera}"

        # check file exists
        assert os.path.exists(file_path), f"segment #{i}: '{file_path}' missing"

        # TODO: this ffprobe call is really slow
        # get width and check frame count
        cmd = f"ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets,width -of csv=p=0 {file_path}"
        if TICI:
          cmd = "LD_LIBRARY_PATH=/usr/local/lib " + cmd

        expected_frames = fps * SEGMENT_LENGTH
        probe = subprocess.check_output(cmd, shell=True, encoding='utf8').split('\n')[0].strip().split(',')
        frame_width, frame_count = int(probe[0]), int(probe[1])
        counts.append(frame_count)

        assert frame_count == expected_frames, \
                         f"segment #{i}: {camera} failed frame count check: expected {expected_frames}, got {frame_count}"

        # sanity check file size
        file_size = os.path.getsize(file_path)
        target_size = size_lambda(frame_width)
        assert math.isclose(file_size, target_size, rel_tol=FILE_SIZE_TOLERANCE), \
                        f"{file_path} size {file_size} isn't close to target size {target_size}"

        # Check encodeIdx
        if encode_idx_name is not None:
          rlog_path = f"{route_prefix_path}--{i}/rlog.zst"
          msgs = [m for m in LogReader(rlog_path) if m.which() == encode_idx_name]
          encode_msgs = [getattr(m, encode_idx_name) for m in msgs]

          valid = [m.valid for m in msgs]
          segment_idxs = [m.segmentId for m in encode_msgs]
          encode_idxs = [m.encodeId for m in encode_msgs]
          frame_idxs = [m.frameId for m in encode_msgs]

          # Check frame count
          assert frame_count == len(segment_idxs)
          assert frame_count == len(encode_idxs)

          # Check for duplicates or skips
          assert 0 == segment_idxs[0]
          assert len(set(segment_idxs)) == len(segment_idxs)

          assert all(valid)

          assert expected_frames * i == encode_idxs[0]
          first_frames.append(frame_idxs[0])
          assert len(set(encode_idxs)) == len(encode_idxs)

      assert 1 == len(set(first_frames))

      if TICI:
        expected_frames = fps * SEGMENT_LENGTH
        assert min(counts) == expected_frames
      shutil.rmtree(f"{route_prefix_path}--{i}")