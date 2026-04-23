def setup_data_readers(
    route: str, sidx: int, needs_driver_cam: bool = True, needs_road_cam: bool = True, dummy_driver_cam: bool = False
) -> tuple[LogReader, dict[str, Any]]:
  lr = LogReader(f"{route}/{sidx}/r")
  frs = {}
  if needs_road_cam:
    frs['roadCameraState'] = FrameReader(get_url(route, str(sidx), "fcamera.hevc"))
    if next((True for m in lr if m.which() == "wideRoadCameraState"), False):
      frs['wideRoadCameraState'] = FrameReader(get_url(route, str(sidx), "ecamera.hevc"))
  if needs_driver_cam:
    if dummy_driver_cam:
      frs['driverCameraState'] = FrameReader(get_url(route, str(sidx), "fcamera.hevc")) # Use fcam as dummy
    else:
      device_type = next(str(msg.initData.deviceType) for msg in lr if msg.which() == "initData")
      assert device_type != "neo", "Driver camera not supported on neo segments. Use dummy dcamera."
      frs['driverCameraState'] = FrameReader(get_url(route, str(sidx), "dcamera.hevc"))

  return lr, frs