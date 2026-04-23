def clip(route: Route, output: str, start: int, end: int, headless: bool = True, big: bool = False,
         title: str | None = None, show_metadata: bool = True, show_time: bool = True, use_qcam: bool = False):
  timer, duration = Timer(), end - start

  import pyray as rl
  if big:
    from openpilot.selfdrive.ui.onroad.augmented_road_view import AugmentedRoadView
  else:
    from openpilot.selfdrive.ui.mici.onroad.augmented_road_view import AugmentedRoadView
  from openpilot.selfdrive.ui.ui_state import ui_state
  from openpilot.system.ui.lib.application import gui_app, FontWeight
  timer.lap("import")

  logger.info(f"Clipping {route.name.canonical_name}, {start}s-{end}s ({duration}s)")
  seg_start, seg_end = start // 60, (end - 1) // 60 + 1
  all_chunks = load_logs_parallel(route.log_paths()[seg_start:seg_end], fps=FRAMERATE)
  timer.lap("logs")

  frame_start = (start - seg_start * 60) * FRAMERATE
  message_chunks = all_chunks[frame_start:frame_start + duration * FRAMERATE]
  if not message_chunks:
    logger.error("No messages to render")
    sys.exit(1)

  if headless:
    rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)

  with OpenpilotPrefix(shared_download_cache=True):
    metadata = load_route_metadata(route) if show_metadata else None
    camera_paths = route.qcamera_paths() if use_qcam else route.camera_paths()
    frame_queue = FrameQueue(camera_paths, start, end, fps=FRAMERATE, use_qcam=use_qcam)

    vipc = VisionIpcServer("camerad")
    vipc.create_buffers(VisionStreamType.VISION_STREAM_ROAD, 4, frame_queue.frame_w, frame_queue.frame_h)
    vipc.start_listener()

    patch_submaster(message_chunks, ui_state)
    gui_app.init_window("clip", fps=FRAMERATE)

    road_view = AugmentedRoadView()
    road_view.set_rect(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
    font = gui_app.font(FontWeight.NORMAL)
    timer.lap("setup")

    frame_idx = 0
    with tqdm.tqdm(total=len(message_chunks), desc="Rendering", unit="frame") as pbar:
      for should_render in gui_app.render():
        if frame_idx >= len(message_chunks):
          break
        _, frame_bytes = frame_queue.get()
        vipc.send(VisionStreamType.VISION_STREAM_ROAD, frame_bytes, frame_idx, int(frame_idx * 5e7), int(frame_idx * 5e7))
        ui_state.update()
        if should_render:
          road_view.render()
          render_overlays(gui_app, font, big, metadata, title, start, frame_idx, show_metadata, show_time)
        frame_idx += 1
        pbar.update(1)
    timer.lap("render")

    frame_queue.stop()
    gui_app.close()
    timer.lap("ffmpeg")

  logger.info(f"Clip saved to: {Path(output).resolve()}")
  logger.info(f"Generated {timer.fmt(duration)}")