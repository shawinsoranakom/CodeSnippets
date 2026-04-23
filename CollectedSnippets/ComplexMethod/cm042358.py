def get_snapshots(frame="roadCameraState", front_frame="driverCameraState"):
  sockets = [s for s in (frame, front_frame) if s is not None]
  sm = messaging.SubMaster(sockets)
  vipc_clients = {s: VisionIpcClient("camerad", VISION_STREAMS[s], True) for s in sockets}

  # wait 4 sec from camerad startup for focus and exposure
  while sm[sockets[0]].frameId < int(4. / DT_MDL):
    sm.update()

  for client in vipc_clients.values():
    client.connect(True)

  # grab images
  rear, front = None, None
  if frame is not None:
    c = vipc_clients[frame]
    rear = extract_image(c.recv())
  if front_frame is not None:
    c = vipc_clients[front_frame]
    front = extract_image(c.recv())
  return rear, front