def generate_html_report(videos: tuple[str, str], basedir: str, different_frames: list[int], frame_counts: tuple[int, int], diff_video_name):
  chunks = []
  if different_frames:
    current_chunk = [different_frames[0]]
    for i in range(1, len(different_frames)):
      if different_frames[i] == different_frames[i - 1] + 1:
        current_chunk.append(different_frames[i])
      else:
        chunks.append(current_chunk)
        current_chunk = [different_frames[i]]
    chunks.append(current_chunk)

  total_frames = max(frame_counts)
  frame_delta = frame_counts[1] - frame_counts[0]
  different_total = len(different_frames) + abs(frame_delta)

  result_text = (
    f"✅ Videos are identical! ({total_frames} frames)"
    if different_total == 0
    else f"❌ Found {different_total} different frames out of {total_frames} total ({different_total / total_frames * 100:.1f}%)."
    + (f" Video {'2' if frame_delta > 0 else '1'} is longer by {abs(frame_delta)} frames." if frame_delta != 0 else "")
  )

  # Load HTML template and replace placeholders
  html = HTML_TEMPLATE_PATH.read_text()
  placeholders = {
    "VIDEO1_SRC": os.path.join(basedir, os.path.basename(videos[0])),
    "VIDEO2_SRC": os.path.join(basedir, os.path.basename(videos[1])),
    "DIFF_SRC": os.path.join(basedir, diff_video_name),
    "RESULT_TEXT": result_text,
  }
  for key, value in placeholders.items():
    html = html.replace(f"${key}", value)

  return html