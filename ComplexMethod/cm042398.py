def wrap_text(text, font_size, max_width):
  lines = []
  font = gui_app.font()

  for paragraph in text.split("\n"):
    if not paragraph.strip():
      # Don't add empty lines first, ensuring wrap_text("") returns []
      if lines:
        lines.append("")
      continue
    indent = re.match(r"^\s*", paragraph).group()
    current_line = indent
    words = re.split(r"(\s+|-)", paragraph[len(indent):])
    while len(words):
      word = words.pop(0)
      test_line = current_line + word + (words.pop(0) if words else "")
      if measure_text_cached(font, test_line, font_size).x <= max_width:
        current_line = test_line
      else:
        lines.append(current_line)
        current_line = word + " "
    current_line = current_line.rstrip()
    if current_line:
      lines.append(current_line)

  return lines