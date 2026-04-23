def render_overlays(gui_app, font, big, metadata, title, start_time, frame_idx, show_metadata, show_time):
  from openpilot.system.ui.lib.text_measure import measure_text_cached
  from openpilot.system.ui.lib.wrap_text import wrap_text
  metadata_size = 16 if big else 12
  title_size = 32 if big else 24
  time_size = 24 if big else 16

  # Time overlay
  time_width = 0
  if show_time:
    t = start_time + frame_idx / FRAMERATE
    time_text = f"{int(t) // 60:02d}:{int(t) % 60:02d}"
    time_width = int(measure_text_cached(font, time_text, time_size).x)
    draw_text_box(time_text, gui_app.width - time_width - 5, 0, time_size, gui_app, font)

  # Metadata overlay (first 5 seconds)
  if show_metadata and metadata and frame_idx < FRAMERATE * 5:
    m = metadata
    text = ", ".join([f"openpilot v{m['version']}", f"route: {m['route']}", f"car: {m['car']}", f"origin: {m['origin']}",
                      f"branch: {m['branch']}", f"commit: {m['commit']}", f"modified: {m['modified']}"])
    # Wrap text if too wide (leave margin on each side)
    margin = 2 * (time_width + 10 if show_time else 20)  # leave enough margin for time overlay
    max_width = gui_app.width - margin
    lines = wrap_text(font, text, metadata_size, max_width)

    # Draw wrapped metadata text
    y_offset = 6
    for line in lines:
      draw_text_box(line, 0, y_offset, metadata_size, gui_app, font, center=True)
      line_height = int(measure_text_cached(font, line, metadata_size).y) + 4
      y_offset += line_height

  # Title overlay
  if title:
    draw_text_box(title, 0, 60, title_size, gui_app, font, center=True)