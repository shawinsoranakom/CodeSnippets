def migrate_cameraStates(msgs):
  add_ops, del_ops = [], []
  frame_to_encode_id = defaultdict(dict)
  # just for encodeId fallback mechanism
  min_frame_id = defaultdict(lambda: float('inf'))

  for _, msg in msgs:
    if msg.which() not in ["roadEncodeIdx", "wideRoadEncodeIdx", "driverEncodeIdx"]:
      continue

    encode_index = getattr(msg, msg.which())
    meta = meta_from_encode_index(msg.which())

    assert encode_index.segmentId < 1200, f"Encoder index segmentId greater that 1200: {msg.which()} {encode_index.segmentId}"
    frame_to_encode_id[meta.camera_state][encode_index.frameId] = encode_index.segmentId

  for index, msg in msgs:
    if msg.which() not in ["roadCameraState", "wideRoadCameraState", "driverCameraState"]:
      continue

    camera_state = getattr(msg, msg.which())
    min_frame_id[msg.which()] = min(min_frame_id[msg.which()], camera_state.frameId)

    encode_id = frame_to_encode_id[msg.which()].get(camera_state.frameId)
    if encode_id is None:
      print(f"Missing encoded frame for camera feed {msg.which()} with frameId: {camera_state.frameId}")
      if len(frame_to_encode_id[msg.which()]) != 0:
        del_ops.append(index)
        continue

      # fallback mechanism for logs without encodeIdx (e.g. logs from before 2022 with dcamera recording disabled)
      # try to fake encode_id by subtracting lowest frameId
      encode_id = camera_state.frameId - min_frame_id[msg.which()]
      print(f"Faking encodeId to {encode_id} for camera feed {msg.which()} with frameId: {camera_state.frameId}")

    new_msg = messaging.new_message(msg.which())
    new_camera_state = getattr(new_msg, new_msg.which())
    new_camera_state.sensor = camera_state.sensor
    new_camera_state.frameId = encode_id
    new_camera_state.encodeId = encode_id
    # timestampSof was added later so it might be missing on some old segments
    if camera_state.timestampSof == 0 and camera_state.timestampEof > 25000000:
      new_camera_state.timestampSof = camera_state.timestampEof - 18000000
    else:
      new_camera_state.timestampSof = camera_state.timestampSof
    new_camera_state.timestampEof = camera_state.timestampEof
    new_msg.logMonoTime = msg.logMonoTime
    new_msg.valid = msg.valid

    del_ops.append(index)
    add_ops.append(new_msg.as_reader())
  return [], add_ops, del_ops