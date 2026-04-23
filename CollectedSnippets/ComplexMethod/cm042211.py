def regen_and_save(
  route: str, sidx: int, processes: str | Iterable[str] = "all", outdir: str = FAKEDATA,
  upload: bool = False, disable_tqdm: bool = False, dummy_driver_cam: bool = False
) -> str:
  if not isinstance(processes, str) and not hasattr(processes, "__iter__"):
    raise ValueError("whitelist_proc must be a string or iterable")

  if processes != "all":
    if isinstance(processes, str):
      raise ValueError(f"Invalid value for processes: {processes}")

    replayed_processes = []
    for d in processes:
      cfg = get_process_config(d)
      replayed_processes.append(cfg)
  else:
    replayed_processes = CONFIGS

  all_vision_pubs = {pub for cfg in replayed_processes for pub in cfg.vision_pubs}
  lr, frs = setup_data_readers(route, sidx,
                               needs_driver_cam="driverCameraState" in all_vision_pubs,
                               needs_road_cam="roadCameraState" in all_vision_pubs or "wideRoadCameraState" in all_vision_pubs,
                               dummy_driver_cam=dummy_driver_cam)
  output_logs = regen_segment(lr, frs, replayed_processes, disable_tqdm=disable_tqdm)

  log_dir = os.path.join(outdir, time.strftime("%Y-%m-%d--%H-%M-%S--0", time.gmtime()))
  rel_log_dir = os.path.relpath(log_dir)
  rpath = os.path.join(log_dir, "rlog.zst")

  os.makedirs(log_dir)
  save_log(rpath, output_logs, compress=True)

  print("\n\n", "*"*30, "\n\n", sep="")
  print("New route:", rel_log_dir, "\n")

  if not check_openpilot_enabled(output_logs):
    raise Exception("Route did not engage for long enough")
  if not check_most_messages_valid(output_logs):
    raise Exception("Route has too many invalid messages")

  if upload:
    upload_route(rel_log_dir)

  return rel_log_dir