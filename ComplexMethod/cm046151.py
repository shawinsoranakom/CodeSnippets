def apply_features(self, raw_frame: np.ndarray, detections: list | None = None) -> np.ndarray:
        """Apply feature-based methods like ORB or SIFT to a raw frame.

        Args:
            raw_frame (np.ndarray): The raw frame to be processed, with shape (H, W, C).
            detections (list, optional): List of detections to be used in the processing.

        Returns:
            (np.ndarray): Transformation matrix with shape (2, 3).

        Examples:
            >>> gmc = GMC(method="orb")
            >>> raw_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            >>> transformation_matrix = gmc.apply_features(raw_frame)
            >>> print(transformation_matrix.shape)
            (2, 3)
        """
        height, width, c = raw_frame.shape
        frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2GRAY) if c == 3 else raw_frame
        H = np.eye(2, 3)

        # Downscale image for computational efficiency
        if self.downscale > 1.0:
            frame = cv2.resize(frame, (width // self.downscale, height // self.downscale))
            width = width // self.downscale
            height = height // self.downscale

        # Create mask for keypoint detection, excluding border regions
        mask = np.zeros_like(frame)
        mask[int(0.02 * height) : int(0.98 * height), int(0.02 * width) : int(0.98 * width)] = 255

        # Exclude detection regions from mask to avoid tracking detected objects
        if detections is not None:
            for det in detections:
                tlbr = (det[:4] / self.downscale).astype(np.int_)
                mask[tlbr[1] : tlbr[3], tlbr[0] : tlbr[2]] = 0

        # Find keypoints and compute descriptors
        keypoints = self.detector.detect(frame, mask)
        keypoints, descriptors = self.extractor.compute(frame, keypoints)

        # Handle first frame initialization
        if not self.initializedFirstFrame:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.prevDescriptors = copy.copy(descriptors)
            self.initializedFirstFrame = True
            return H

        # Match descriptors between previous and current frame
        knnMatches = self.matcher.knnMatch(self.prevDescriptors, descriptors, 2)

        # Filter matches based on spatial distance constraints
        matches = []
        spatialDistances = []
        maxSpatialDistance = 0.25 * np.array([width, height])

        # Handle empty matches case
        if len(knnMatches) == 0:
            self.prevFrame = frame.copy()
            self.prevKeyPoints = copy.copy(keypoints)
            self.prevDescriptors = copy.copy(descriptors)
            return H

        # Apply Lowe's ratio test and spatial distance filtering
        for m, n in knnMatches:
            if m.distance < 0.9 * n.distance:
                prevKeyPointLocation = self.prevKeyPoints[m.queryIdx].pt
                currKeyPointLocation = keypoints[m.trainIdx].pt

                spatialDistance = (
                    prevKeyPointLocation[0] - currKeyPointLocation[0],
                    prevKeyPointLocation[1] - currKeyPointLocation[1],
                )

                if (np.abs(spatialDistance[0]) < maxSpatialDistance[0]) and (
                    np.abs(spatialDistance[1]) < maxSpatialDistance[1]
                ):
                    spatialDistances.append(spatialDistance)
                    matches.append(m)

        # Filter outliers using statistical analysis
        meanSpatialDistances = np.mean(spatialDistances, 0)
        stdSpatialDistances = np.std(spatialDistances, 0)
        inliers = (spatialDistances - meanSpatialDistances) < 2.5 * stdSpatialDistances

        # Extract good matches and corresponding points
        goodMatches = []
        prevPoints = []
        currPoints = []
        for i in range(len(matches)):
            if inliers[i, 0] and inliers[i, 1]:
                goodMatches.append(matches[i])
                prevPoints.append(self.prevKeyPoints[matches[i].queryIdx].pt)
                currPoints.append(keypoints[matches[i].trainIdx].pt)

        prevPoints = np.array(prevPoints)
        currPoints = np.array(currPoints)

        # Estimate transformation matrix using RANSAC
        if prevPoints.shape[0] > 4:
            H, inliers = cv2.estimateAffinePartial2D(prevPoints, currPoints, cv2.RANSAC)

            # Scale translation components back to original resolution
            if self.downscale > 1.0:
                H[0, 2] *= self.downscale
                H[1, 2] *= self.downscale
        else:
            LOGGER.warning("not enough matching points")

        # Store current frame data for next iteration
        self.prevFrame = frame.copy()
        self.prevKeyPoints = copy.copy(keypoints)
        self.prevDescriptors = copy.copy(descriptors)

        return H