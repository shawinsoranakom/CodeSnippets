def apply_sparseoptflow(self, raw_frame: np.ndarray) -> np.ndarray:
        """Apply Sparse Optical Flow method to a raw frame.

        Args:
            raw_frame (np.ndarray): The raw frame to be processed, with shape (H, W, C).

        Returns:
            (np.ndarray): Transformation matrix with shape (2, 3).

        Examples:
            >>> gmc = GMC()
            >>> result = gmc.apply_sparseoptflow(np.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]]))
            >>> print(result)
            [[1. 0. 0.]
             [0. 1. 0.]]
        """
        height, width, c = raw_frame.shape
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY) if c == 3 else raw_frame
        H = np.eye(2, 3)

        # Downscale image for computational efficiency
        if self.downscale > 1.0:
            frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))

        # Find good features to track
        keypoints = cv2.goodFeaturesToTrack(frame, mask=None, **self.feature_params)

        # Handle first frame initialization
        if not self.initializedFirstFrame or self.prevKeyPoints is None:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.initializedFirstFrame = True
            return H

        # Calculate optical flow using Lucas-Kanade method
        matchedKeypoints, status, _ = cv2.calcOpticalFlowPyrLK(self.prevFrame, frame, self.prevKeyPoints, None)

        # Extract successfully tracked points
        prevPoints = []
        currPoints = []

        for i in range(len(status)):
            if status[i]:
                prevPoints.append(self.prevKeyPoints[i])
                currPoints.append(matchedKeypoints[i])

        prevPoints = np.array(prevPoints)
        currPoints = np.array(currPoints)

        # Estimate transformation matrix using RANSAC
        if (prevPoints.shape[0] > 4) and (prevPoints.shape[0] == currPoints.shape[0]):
            H, _ = cv2.estimateAffinePartial2D(prevPoints, currPoints, cv2.RANSAC)

            # Scale translation components back to original resolution
            if self.downscale > 1.0:
                H[0, 2] *= self.downscale
                H[1, 2] *= self.downscale
        else:
            LOGGER.warning("not enough matching points")

        # Store current frame data for next iteration
        self.prevFrame = frame.copy()
        self.prevKeyPoints = copy.copy(keypoints)

        return H