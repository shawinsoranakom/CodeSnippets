def _publish_camera_and_audio_messages(self, num_segs=1, segment_length=5):
    # Use small frame sizes for testing (width, height, size, stride, uv_offset)
    # NV12 format: size = stride * height * 1.5, uv_offset = stride * height
    w, h = 320, 240
    frame_spec = (w, h, w * h * 3 // 2, w, w * h)
    streams = [
      (VisionStreamType.VISION_STREAM_ROAD, frame_spec, "roadCameraState"),
      (VisionStreamType.VISION_STREAM_DRIVER, frame_spec, "driverCameraState"),
      (VisionStreamType.VISION_STREAM_WIDE_ROAD, frame_spec, "wideRoadCameraState"),
    ]

    sm = messaging.SubMaster(["roadEncodeData"])
    pm = messaging.PubMaster([s for _, _, s in streams] + ["rawAudioData"])
    vipc_server = VisionIpcServer("camerad")
    for stream_type, frame_spec, _ in streams:
      vipc_server.create_buffers_with_sizes(stream_type, 40, *(frame_spec))
    vipc_server.start_listener()

    os.environ["LOGGERD_TEST"] = "1"
    os.environ["LOGGERD_SEGMENT_LENGTH"] = str(segment_length)
    managed_processes["loggerd"].start()
    managed_processes["encoderd"].start()
    assert pm.wait_for_readers_to_update("roadCameraState", timeout=5)

    fps = 20
    for n in range(1, int(num_segs * segment_length * fps) + 1):
      # send video
      for stream_type, frame_spec, state in streams:
        dat = np.empty(frame_spec[2], dtype=np.uint8)
        vipc_server.send(stream_type, dat[:].flatten().tobytes(), n, n / fps, n / fps)

        camera_state = messaging.new_message(state)
        frame = getattr(camera_state, state)
        frame.frameId = n
        pm.send(state, camera_state)

      # send audio
      msg = messaging.new_message('rawAudioData')
      msg.rawAudioData.data = bytes(800 * 2) # 800 samples of int16
      msg.rawAudioData.sampleRate = 16000
      pm.send('rawAudioData', msg)

      for _, _, state in streams:
        assert pm.wait_for_readers_to_update(state, timeout=5, dt=0.001)

      sm.update(100)  # wait for encode data publish

    managed_processes["loggerd"].stop()
    managed_processes["encoderd"].stop()