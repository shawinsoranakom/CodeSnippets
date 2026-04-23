def _icon_helper(self, alert: Alert) -> AlertLayout:
    icon_side = None
    txt_icon = None
    icon_margin_x = 20
    icon_margin_y = 18

    # alert_type format is "EventName/eventType" (e.g., "preLaneChangeLeft/warning")
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''

    if event_name == 'preLaneChangeLeft':
      icon_side = IconSide.left
      txt_icon = self._txt_turn_signal_left
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'preLaneChangeRight':
      icon_side = IconSide.right
      txt_icon = self._txt_turn_signal_right
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'laneChange':
      icon_side = self._last_icon_side
      txt_icon = self._txt_turn_signal_left if self._last_icon_side == 'left' else self._txt_turn_signal_right
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'laneChangeBlocked':
      CS = ui_state.sm['carState']
      if CS.leftBlinker:
        icon_side = IconSide.left
      elif CS.rightBlinker:
        icon_side = IconSide.right
      else:
        icon_side = self._last_icon_side
      txt_icon = self._txt_blind_spot_left if icon_side == 'left' else self._txt_blind_spot_right
      icon_margin_x = 8
      icon_margin_y = 0

    else:
      self._turn_signal_timer = 0.0

    self._last_icon_side = icon_side

    # create text rect based on icon presence
    text_x = self._rect.x + ALERT_MARGIN
    text_width = self._rect.width - ALERT_MARGIN
    if icon_side == 'left':
      text_x = self._rect.x + self._txt_turn_signal_right.width
      text_width = self._rect.width - ALERT_MARGIN - self._txt_turn_signal_right.width
    elif icon_side == 'right':
      text_x = self._rect.x + ALERT_MARGIN
      text_width = self._rect.width - ALERT_MARGIN - self._txt_turn_signal_right.width

    text_rect = rl.Rectangle(
      text_x,
      self._alert_y_filter.x,
      text_width,
      self._rect.height,
    )
    icon_layout = IconLayout(txt_icon, icon_side, icon_margin_x, icon_margin_y) if txt_icon is not None and icon_side is not None else None
    return AlertLayout(text_rect, icon_layout)