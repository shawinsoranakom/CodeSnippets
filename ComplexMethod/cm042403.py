def _render(self, rect: rl.Rectangle):
    # TODO: speed up by removing duplicate calculations across renders
    current_y = rect.y
    padding = 20
    content_width = rect.width - (padding * 2)

    for element in self.elements:
      if element.type == ElementType.BR:
        current_y += element.margin_bottom
        continue

      current_y += element.margin_top
      if current_y > rect.y + rect.height:
        break

      if element.content:
        font = self._get_font(element.font_weight)
        wrapped_lines = wrap_text(font, element.content, element.font_size, int(content_width))

        for line in wrapped_lines:
          # Use FONT_SCALE from wrapped raylib text functions to match what is drawn
          if current_y < rect.y - element.font_size * FONT_SCALE:
            current_y += element.font_size * FONT_SCALE * element.line_height
            continue

          if current_y > rect.y + rect.height:
            break

          if self._center_text:
            text_width = measure_text_cached(font, line, element.font_size).x
            text_x = rect.x + (rect.width - text_width) / 2
          else:  # left align
            text_x = rect.x + (max(element.indent_level - 1, 0) * LIST_INDENT_PX)

          rl.draw_text_ex(font, line, rl.Vector2(text_x + padding, current_y), element.font_size, 0, self._text_color)

          current_y += element.font_size * FONT_SCALE * element.line_height

      # Apply bottom margin
      current_y += element.margin_bottom

    return current_y - rect.y