def _draw_text(self, alert: Alert, alert_layout: AlertLayout) -> None:
    icon_side = alert_layout.icon.side if alert_layout.icon is not None else None

    # TODO: hack
    alert_text1 = alert.text1.lower().replace('calibrating: ', 'calibrating:\n')
    can_draw_second_line = False
    # TODO: there should be a common way to determine font size based on text length to maximize rect
    if len(alert_text1) <= 12:
      can_draw_second_line = True
      font_size = 92 - 10
    elif len(alert_text1) <= 16:
      can_draw_second_line = True
      font_size = 70
    else:
      font_size = 64 - 10

    if icon_side is not None:
      font_size -= 10

    color = rl.Color(255, 255, 255, int(255 * 0.9 * self._alpha_filter.x))

    text1_y_offset = 11 if font_size >= 70 else 4
    text_rect1 = rl.Rectangle(
      alert_layout.text_rect.x,
      alert_layout.text_rect.y - text1_y_offset,
      alert_layout.text_rect.width,
      alert_layout.text_rect.height,
    )
    self._alert_text1_label.set_text(alert_text1)
    self._alert_text1_label.set_text_color(color)
    self._alert_text1_label.set_font_size(font_size)
    self._alert_text1_label.set_alignment(rl.GuiTextAlignment.TEXT_ALIGN_LEFT if icon_side != 'left' else rl.GuiTextAlignment.TEXT_ALIGN_RIGHT)
    self._alert_text1_label.render(text_rect1)

    alert_text2 = alert.text2.lower()

    # randomize chars and length for testing
    if DEBUG:
      if time.monotonic() - self._text_gen_time > 0.5:
        self._alert_text2_gen = ''.join(random.choices(string.ascii_lowercase + ' ', k=random.randint(0, 40)))
        self._text_gen_time = time.monotonic()
      alert_text2 = self._alert_text2_gen or alert_text2

    if can_draw_second_line and alert_text2:
      last_line_h = self._alert_text1_label.rect.y + self._alert_text1_label.get_content_height(int(alert_layout.text_rect.width))
      last_line_h -= 4
      if len(alert_text2) > 18:
        small_font_size = 36
      elif len(alert_text2) > 24:
        small_font_size = 32
      else:
        small_font_size = 40
      text_rect2 = rl.Rectangle(
        alert_layout.text_rect.x,
        last_line_h,
        alert_layout.text_rect.width,
        alert_layout.text_rect.height - last_line_h
      )
      color = rl.Color(255, 255, 255, int(255 * 0.65 * self._alpha_filter.x))

      self._alert_text2_label.set_text(alert_text2)
      self._alert_text2_label.set_text_color(color)
      self._alert_text2_label.set_font_size(small_font_size)
      self._alert_text2_label.set_alignment(rl.GuiTextAlignment.TEXT_ALIGN_LEFT if icon_side != 'left' else rl.GuiTextAlignment.TEXT_ALIGN_RIGHT)
      self._alert_text2_label.render(text_rect2)