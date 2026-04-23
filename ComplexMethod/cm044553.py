def on_hover(self, event: tk.Event | None) -> None:
        """ Highlight the face and set the mouse cursor for the mouse's current location.

        Parameters
        ----------
        event: :class:`tkinter.Event` or ``None``
            The tkinter mouse event. Provides the current location of the mouse cursor. If ``None``
            is passed as the event (for example when this function is being called outside of a
            mouse event) then the location of the cursor will be calculated
        """
        if event is None:
            pnts = np.array((self._canvas.winfo_pointerx(), self._canvas.winfo_pointery()))
            pnts -= np.array((self._canvas.winfo_rootx(), self._canvas.winfo_rooty()))
        else:
            pnts = np.array((event.x, event.y))

        coords = (int(self._canvas.canvasx(pnts[0])), int(self._canvas.canvasy(pnts[1])))
        face = self._viewport.face_from_point(*coords)
        frame_idx, face_idx = face[:2]

        if frame_idx == self._current_frame_index and face_idx == self._current_face_index:
            return

        is_zoomed = self._globals.is_zoomed
        if (-1 in face or (frame_idx == self._globals.frame_index
                           and (not is_zoomed or
                                (is_zoomed and face_idx == self._globals.face_index)))):
            self._clear()
            self._canvas.config(cursor="")
            self._current_frame_index = None
            self._current_face_index = None
            return

        logger.debug("Viewport hover: frame_idx: %s, face_idx: %s", frame_idx, face_idx)

        self._canvas.config(cursor="hand2")
        self._highlight(face[2:])
        self._current_frame_index = frame_idx
        self._current_face_index = face_idx