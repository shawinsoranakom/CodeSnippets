def _render(self, _):
    if not self.alert_data.visible or not self.alert_data.text:
      return

    # Choose background based on size
    if self._alert_size == AlertSize.BIG:
      bg_texture = self._bg_big_pressed if self.is_pressed else self._bg_big
    elif self._alert_size == AlertSize.MEDIUM:
      bg_texture = self._bg_medium_pressed if self.is_pressed else self._bg_medium
    else:  # AlertSize.SMALL
      bg_texture = self._bg_small_pressed if self.is_pressed else self._bg_small

    # Draw background
    rl.draw_texture_ex(bg_texture, rl.Vector2(self._rect.x, self._rect.y), 0.0, 1.0, rl.WHITE)

    # Calculate text area (left side, avoiding icon on right)
    title_width = self.ALERT_WIDTH - (self.ALERT_PADDING * 2) - self.ICON_SIZE - self.ICON_MARGIN
    body_width = self.ALERT_WIDTH - (self.ALERT_PADDING * 2)
    text_x = self._rect.x + self.ALERT_PADDING
    text_y = self._rect.y + self.ALERT_PADDING

    # Draw title label
    if self._title_text:
      title_rect = rl.Rectangle(
        text_x,
        text_y,
        title_width,
        self._title_label.get_content_height(title_width),
      )
      self._title_label.render(title_rect)
      text_y += title_rect.height + self.TITLE_BODY_SPACING

    # Draw body label
    if self._body_text:
      body_rect = rl.Rectangle(
        text_x,
        text_y,
        body_width,
        self._rect.height - text_y + self._rect.y - self.ALERT_PADDING,
      )
      self._body_label.render(body_rect)

    # Draw warning icon on the right side
    # Use green icon for update alerts (severity = -1), red for high severity, orange for low severity
    if self.alert_data.severity == -1:
      icon_texture = self._icon_green
    elif self.alert_data.severity > 0:
      icon_texture = self._icon_red
    else:
      icon_texture = self._icon_orange
    icon_x = self._rect.x + self.ALERT_WIDTH - self.ALERT_PADDING - self.ICON_SIZE
    icon_y = self._rect.y + self.ALERT_PADDING
    rl.draw_texture_ex(icon_texture, rl.Vector2(icon_x, icon_y), 0.0, 1.0, rl.WHITE)