def _disable_enable_copy_buttons(self, *args):  # pylint:disable=unused-argument
        """ Disable or enable the static buttons """
        position = self._globals.frame_index
        face_count_per_index = self._det_faces.face_count_per_index
        prev_exists = position != -1 and any(count != 0
                                             for count in face_count_per_index[:position])
        next_exists = position != -1 and any(count != 0
                                             for count in face_count_per_index[position + 1:])
        states = {"prev": ["!disabled"] if prev_exists else ["disabled"],
                  "next": ["!disabled"] if next_exists else ["disabled"]}
        for direction in ("prev", "next"):
            self._static_buttons[f"copy_{direction}"].state(states[direction])