def _handle_mouse_release(self, mouse_pos: MousePos):
    if self._closest_key[0] is not None:
      if self._closest_key[0] == self._caps_key:
        self._set_uppercase(True)
      elif self._closest_key[0] in (self._123_key, self._123_key2):
        self._set_keys(self._special_keys)
      elif self._closest_key[0] == self._abc_key:
        self._set_uppercase(False)
      elif self._closest_key[0] == self._super_special_key:
        self._set_keys(self._super_special_keys)
      else:
        self._text += self._closest_key[0].char

        # Reset caps state
        if self._caps_state == CapsState.UPPER:
          self._set_uppercase(False)

        # Switch back to letters after common URL delimiters
        if self._closest_key[0].char in self._auto_return_to_letters and self._current_keys in (self._special_keys, self._super_special_keys):
          self._set_uppercase(False)

    # ensure minimum selected animation time
    key_selected_dt = rl.get_time() - (self._selected_key_t or 0)
    cur_t = rl.get_time()
    self._unselect_key_t = cur_t + KEY_MIN_ANIMATION_TIME if (key_selected_dt < KEY_MIN_ANIMATION_TIME) else cur_t