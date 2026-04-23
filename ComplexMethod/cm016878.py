def draw_wholebody_keypoints(self, canvas, keypoints, scores=None, threshold=0.3,
                                 draw_body=True, draw_feet=True, draw_face=True, draw_hands=True, stick_width=4, face_point_size=3):
        """
        Draw wholebody keypoints (134 keypoints after processing) in DWPose style.

        Expected keypoint format (after neck insertion and remapping):
        - Body: 0-17 (18 keypoints in OpenPose format, neck at index 1)
        - Foot: 18-23 (6 keypoints)
        - Face: 24-91 (68 landmarks)
        - Right hand: 92-112 (21 keypoints)
        - Left hand: 113-133 (21 keypoints)

        Args:
            canvas: The canvas to draw on (numpy array)
            keypoints: Array of keypoint coordinates
            scores: Optional confidence scores for each keypoint
            threshold: Minimum confidence threshold for drawing keypoints

        Returns:
            canvas: The canvas with keypoints drawn
        """
        H, W, C = canvas.shape

        # Draw body limbs
        if draw_body and len(keypoints) >= 18:
            for i, limb in enumerate(self.body_limbSeq):
                # Convert from 1-indexed to 0-indexed
                idx1, idx2 = limb[0] - 1, limb[1] - 1

                if idx1 >= 18 or idx2 >= 18:
                    continue

                if scores is not None:
                    if scores[idx1] < threshold or scores[idx2] < threshold:
                        continue

                Y = [keypoints[idx1][0], keypoints[idx2][0]]
                X = [keypoints[idx1][1], keypoints[idx2][1]]
                mX, mY = (X[0] + X[1]) / 2, (Y[0] + Y[1]) / 2
                length = math.sqrt((X[0] - X[1]) ** 2 + (Y[0] - Y[1]) ** 2)

                if length < 1:
                    continue

                angle = math.degrees(math.atan2(X[0] - X[1], Y[0] - Y[1]))

                polygon = self.draw.ellipse2Poly((int(mY), int(mX)), (int(length / 2), stick_width), int(angle), 0, 360, 1)

                self.draw.fillConvexPoly(canvas, polygon, self.colors[i % len(self.colors)])

        # Draw body keypoints
        if draw_body and len(keypoints) >= 18:
            for i in range(18):
                if scores is not None and scores[i] < threshold:
                    continue
                x, y = int(keypoints[i][0]), int(keypoints[i][1])
                if 0 <= x < W and 0 <= y < H:
                    self.draw.circle(canvas, (x, y), 4, self.colors[i % len(self.colors)], thickness=-1)

        # Draw foot keypoints (18-23, 6 keypoints)
        if draw_feet and len(keypoints) >= 24:
            for i in range(18, 24):
                if scores is not None and scores[i] < threshold:
                    continue
                x, y = int(keypoints[i][0]), int(keypoints[i][1])
                if 0 <= x < W and 0 <= y < H:
                    self.draw.circle(canvas, (x, y), 4, self.colors[i % len(self.colors)], thickness=-1)

        # Draw right hand (92-112)
        if draw_hands and len(keypoints) >= 113:
            eps = 0.01
            for ie, edge in enumerate(self.hand_edges):
                idx1, idx2 = 92 + edge[0], 92 + edge[1]
                if scores is not None:
                    if scores[idx1] < threshold or scores[idx2] < threshold:
                        continue

                x1, y1 = int(keypoints[idx1][0]), int(keypoints[idx1][1])
                x2, y2 = int(keypoints[idx2][0]), int(keypoints[idx2][1])

                if x1 > eps and y1 > eps and x2 > eps and y2 > eps:
                    if 0 <= x1 < W and 0 <= y1 < H and 0 <= x2 < W and 0 <= y2 < H:
                        # HSV to RGB conversion for rainbow colors
                        r, g, b = colorsys.hsv_to_rgb(ie / float(len(self.hand_edges)), 1.0, 1.0)
                        color = (int(r * 255), int(g * 255), int(b * 255))
                        self.draw.line(canvas, (x1, y1), (x2, y2), color, thickness=2)

            # Draw right hand keypoints
            for i in range(92, 113):
                if scores is not None and scores[i] < threshold:
                    continue
                x, y = int(keypoints[i][0]), int(keypoints[i][1])
                if x > eps and y > eps and 0 <= x < W and 0 <= y < H:
                    self.draw.circle(canvas, (x, y), 4, (0, 0, 255), thickness=-1)

        # Draw left hand (113-133)
        if draw_hands and len(keypoints) >= 134:
            eps = 0.01
            for ie, edge in enumerate(self.hand_edges):
                idx1, idx2 = 113 + edge[0], 113 + edge[1]
                if scores is not None:
                    if scores[idx1] < threshold or scores[idx2] < threshold:
                        continue

                x1, y1 = int(keypoints[idx1][0]), int(keypoints[idx1][1])
                x2, y2 = int(keypoints[idx2][0]), int(keypoints[idx2][1])

                if x1 > eps and y1 > eps and x2 > eps and y2 > eps:
                    if 0 <= x1 < W and 0 <= y1 < H and 0 <= x2 < W and 0 <= y2 < H:
                        # HSV to RGB conversion for rainbow colors
                        r, g, b = colorsys.hsv_to_rgb(ie / float(len(self.hand_edges)), 1.0, 1.0)
                        color = (int(r * 255), int(g * 255), int(b * 255))
                        self.draw.line(canvas, (x1, y1), (x2, y2), color, thickness=2)

            # Draw left hand keypoints
            for i in range(113, 134):
                if scores is not None and i < len(scores) and scores[i] < threshold:
                    continue
                x, y = int(keypoints[i][0]), int(keypoints[i][1])
                if x > eps and y > eps and 0 <= x < W and 0 <= y < H:
                    self.draw.circle(canvas, (x, y), 4, (0, 0, 255), thickness=-1)

        # Draw face keypoints (24-91) - white dots only, no lines
        if draw_face and len(keypoints) >= 92:
            eps = 0.01
            for i in range(24, 92):
                if scores is not None and scores[i] < threshold:
                    continue
                x, y = int(keypoints[i][0]), int(keypoints[i][1])
                if x > eps and y > eps and 0 <= x < W and 0 <= y < H:
                    self.draw.circle(canvas, (x, y), face_point_size, (255, 255, 255), thickness=-1)

        return canvas