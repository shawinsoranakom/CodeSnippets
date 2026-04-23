def _process_mouse_events(self) -> None:
    hit_rect = self._hit_rect
    touch_valid = self._touch_valid()

    for mouse_event in gui_app.mouse_events:
      if not self._multi_touch and mouse_event.slot != 0:
        continue

      mouse_in_rect = rl.check_collision_point_rec(mouse_event.pos, hit_rect)
      # Ignores touches/presses that start outside our rect
      # Allows touch to leave the rect and come back in focus if mouse did not release
      if mouse_event.left_pressed and touch_valid:
        if mouse_in_rect:
          self._handle_mouse_press(mouse_event.pos)
          self.__is_pressed[mouse_event.slot] = True
          self.__tracking_is_pressed[mouse_event.slot] = True
          self._handle_mouse_event(mouse_event)

      # Callback such as scroll panel signifies user is scrolling
      elif not touch_valid:
        self.__is_pressed[mouse_event.slot] = False
        self.__tracking_is_pressed[mouse_event.slot] = False

      elif mouse_event.left_released:
        self._handle_mouse_event(mouse_event)
        if self.__is_pressed[mouse_event.slot] and mouse_in_rect:
          self._handle_mouse_release(mouse_event.pos)
        self.__is_pressed[mouse_event.slot] = False
        self.__tracking_is_pressed[mouse_event.slot] = False

      # Mouse/touch is still within our rect
      elif mouse_in_rect:
        if self.__tracking_is_pressed[mouse_event.slot]:
          self.__is_pressed[mouse_event.slot] = True
          self._handle_mouse_event(mouse_event)

      # Mouse/touch left our rect but may come back into focus later
      elif not mouse_in_rect:
        self.__is_pressed[mouse_event.slot] = False
        self._handle_mouse_event(mouse_event)