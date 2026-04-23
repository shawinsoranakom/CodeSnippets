def main():
  config_realtime_process(7, 5)

  model = ModelState()
  cloudlog.warning("models loaded, dmonitoringmodeld starting")

  cloudlog.warning("connecting to driver stream")
  vipc_client = VisionIpcClient("camerad", VisionStreamType.VISION_STREAM_DRIVER, True)
  while not vipc_client.connect(False):
    time.sleep(0.1)
  assert vipc_client.is_connected()
  cloudlog.warning(f"connected with buffer size: {vipc_client.buffer_len}")

  sm = SubMaster(["liveCalibration"])
  pm = PubMaster(["driverStateV2"])

  calib = np.zeros(model.numpy_inputs['calib'].size, dtype=np.float32)
  model_transform = None

  while True:
    buf = vipc_client.recv()
    if buf is None:
      continue

    if model_transform is None:
      cam = _os_fisheye if buf.width == _os_fisheye.width else _ar_ox_fisheye
      model_transform = np.linalg.inv(np.dot(dmonitoringmodel_intrinsics, np.linalg.inv(cam.intrinsics))).astype(np.float32)

    sm.update(0)
    if sm.updated["liveCalibration"]:
      calib[:] = np.array(sm["liveCalibration"].rpyCalib)

    t1 = time.perf_counter()
    model_output, gpu_execution_time = model.run(buf, calib, model_transform)
    t2 = time.perf_counter()
    raw_pred = model_output.tobytes() if SEND_RAW_PRED else b''
    model_output = slice_outputs(model_output, model.output_slices)
    model_output = parse_model_output(model_output)
    model_output['raw_pred'] = raw_pred
    msg = get_driverstate_packet(model_output, vipc_client.frame_id, vipc_client.timestamp_sof, t2 - t1, gpu_execution_time)
    pm.send("driverStateV2", msg)