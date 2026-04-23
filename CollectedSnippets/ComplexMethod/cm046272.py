def mouse_event_for_distance(self, event: int, x: int, y: int, flags: int, param: Any) -> None:
        """Handle mouse events to select regions in a real-time video stream for distance calculation.

        Args:
            event (int): Type of mouse event (e.g., cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN).
            x (int): X-coordinate of the mouse pointer.
            y (int): Y-coordinate of the mouse pointer.
            flags (int): Flags associated with the event (e.g., cv2.EVENT_FLAG_CTRLKEY, cv2.EVENT_FLAG_SHIFTKEY).
            param (Any): Additional parameters passed to the function.

        Examples:
            >>> # Assuming 'dc' is an instance of DistanceCalculation
            >>> cv2.setMouseCallback("window_name", dc.mouse_event_for_distance)
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.left_mouse_count += 1
            if self.left_mouse_count <= 2:
                for box, track_id in zip(self.boxes, self.track_ids):
                    if box[0] < x < box[2] and box[1] < y < box[3] and track_id not in self.selected_boxes:
                        self.selected_boxes[track_id] = box

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.selected_boxes = {}
            self.left_mouse_count = 0