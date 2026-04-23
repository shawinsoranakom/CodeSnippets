def _update_cursor(self, event):
        """ Set the cursor action.

        Launch the cursor update action for the currently selected edit mode.

        Parameters
        ----------
        event: :class:`tkinter.Event`
            The current tkinter mouse event
        """
        self._hide_labels()
        if self._drag_data:
            self._update_cursor_select_mode(event)
        else:
            objs = self._canvas.find_withtag(f"lm_grb_face_{self._globals.face_index}"
                                             if self._globals.is_zoomed else "lm_grb")
            item_ids = set(self._canvas.find_overlapping(event.x - 6,
                                                         event.y - 6,
                                                         event.x + 6,
                                                         event.y + 6)).intersection(objs)
            bboxes = [self._canvas.bbox(idx) for idx in item_ids]
            item_id = next((idx for idx, bbox in zip(item_ids, bboxes)
                            if bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]),
                           None)
            if item_id:
                self._update_cursor_point_mode(item_id)
            else:
                self._canvas.config(cursor="")
                self._mouse_location = None