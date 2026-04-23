def run_replay(variant: LayoutVariant) -> None:
  if HEADLESS:
    rl.set_config_flags(rl.ConfigFlags.FLAG_WINDOW_HIDDEN)
    os.environ["OFFSCREEN"] = "1"  # Run UI without FPS limit (set before importing gui_app)

  setup_state()
  os.makedirs(DIFF_OUT_DIR, exist_ok=True)

  from openpilot.selfdrive.ui.ui_state import ui_state, device  # Import within OpenpilotPrefix context so param values are setup correctly
  from openpilot.system.ui.lib.application import gui_app  # Import here for accurate coverage
  from openpilot.selfdrive.ui.tests.diff.replay_script import build_script

  gui_app.init_window("ui diff test", fps=FPS)

  # Dynamically import main layout based on variant
  if variant == "mici":
    from openpilot.selfdrive.ui.mici.layouts.main import MiciMainLayout as MainLayout
  else:
    from openpilot.selfdrive.ui.layouts.main import MainLayout
  main_layout = MainLayout()

  # Disable interactive timeout — replay clicks use left_down=False so they never reset the timer,
  # and after 30s of real wall-clock time the settings panel would close automatically.
  device.set_override_interactive_timeout(99999)

  pm = PubMaster(["deviceState", "pandaStates", "driverStateV2", "selfdriveState"])
  script = build_script(pm, main_layout, variant)
  script_index = 0

  send_fn: Callable | None = None
  frame = 0
  # Override raylib timing functions to return deterministic values based on frame count instead of real time
  rl.get_frame_time = lambda: 1.0 / FPS
  rl.get_time = lambda: frame / FPS

  # Main loop to replay events and render frames
  with tqdm(total=script[-1][0] + 1, desc="Replaying", unit="frame", disable=bool(os.getenv("CI"))) as pbar:
    for _ in gui_app.render():
      # Handle all events for the current frame
      while script_index < len(script) and script[script_index][0] == frame:
        _, event = script[script_index]
        # Call setup function, if any
        if event.setup:
          event.setup()
        # Send mouse events to the application
        if event.mouse_events:
          with gui_app._mouse._lock:
            gui_app._mouse._events.extend(event.mouse_events)
        # Update persistent send function
        if event.send_fn is not None:
          send_fn = event.send_fn
        # Move to next script event
        script_index += 1

      # Keep sending cereal messages for persistent states (onroad, alerts)
      if send_fn:
        send_fn()

      ui_state.update()

      frame += 1
      pbar.update(1)

      if script_index >= len(script):
        break

  gui_app.close()

  print(f"Total frames: {frame}")
  print(f"Video saved to: {os.environ['RECORD_OUTPUT']}")