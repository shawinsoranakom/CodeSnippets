def _update_content(self):
    """Update text and calculate height."""
    if not self.alert_data.visible or not self.alert_data.text:
      self.set_visible(False)
      return

    self.set_visible(True)

    # Split text into title and body
    self._title_text, self._body_text = self._split_text(self.alert_data.text)

    # Calculate text width (alert width minus padding and icon space on right)
    title_width = self.ALERT_WIDTH - (self.ALERT_PADDING * 2) - self.ICON_SIZE - self.ICON_MARGIN
    body_width = self.ALERT_WIDTH - (self.ALERT_PADDING * 2)

    # Update labels
    self._title_label.set_text(self._title_text)
    self._body_label.set_text(self._body_text)

    # Calculate content height
    title_height = self._title_label.get_content_height(title_width) if self._title_text else 0
    body_height = self._body_label.get_content_height(body_width) if self._body_text else 0
    spacing = self.TITLE_BODY_SPACING if (self._title_text and self._body_text) else 0
    total_text_height = title_height + spacing + body_height

    # Determine which background size to use based on content height
    min_height_with_padding = total_text_height + (self.ALERT_PADDING * 2)
    if min_height_with_padding > self.ALERT_HEIGHT_MED:
      self._alert_size = AlertSize.BIG
      height = self.ALERT_HEIGHT_BIG
    elif min_height_with_padding > self.ALERT_HEIGHT_SMALL:
      self._alert_size = AlertSize.MEDIUM
      height = self.ALERT_HEIGHT_MED
    else:
      self._alert_size = AlertSize.SMALL
      height = self.ALERT_HEIGHT_SMALL

    # Set rect size
    self.set_rect(rl.Rectangle(0, 0, self.ALERT_WIDTH, height))