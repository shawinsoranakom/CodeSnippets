def process(self, im0) -> SolutionResults:
        """Monitor workouts using Ultralytics YOLO Pose Model.

        This function processes an input image to track and analyze human poses for workout monitoring. It uses the YOLO
        Pose model to detect keypoints, estimate angles, and count repetitions based on predefined angle thresholds.

        Args:
            im0 (np.ndarray): Input image for processing.

        Returns:
            (SolutionResults): Contains processed image `plot_im`, 'workout_count' (list of completed reps),
                'workout_stage' (list of current stages), 'workout_angle' (list of angles), and 'total_tracks' (total
                number of tracked individuals).

        Examples:
            >>> gym = AIGym()
            >>> image = cv2.imread("workout.jpg")
            >>> results = gym.process(image)
            >>> processed_image = results.plot_im
        """
        annotator = SolutionAnnotator(im0, line_width=self.line_width)  # Initialize annotator

        self.extract_tracks(im0)  # Extract tracks (bounding boxes, classes, and masks)

        if len(self.boxes):
            kpt_data = self.tracks.keypoints.data

            for i, k in enumerate(kpt_data):
                state = self.states[self.track_ids[i]]  # get state details
                # Get keypoints and estimate the angle
                state["angle"] = annotator.estimate_pose_angle(*[k[int(idx)] for idx in self.kpts])
                annotator.draw_specific_kpts(k, self.kpts, radius=self.line_width * 3)

                # Determine stage and count logic based on angle thresholds
                if state["angle"] < self.down_angle:
                    if state["stage"] == "up":
                        state["count"] += 1
                    state["stage"] = "down"
                elif state["angle"] > self.up_angle:
                    state["stage"] = "up"

                # Display angle, count, and stage text
                if self.show_labels:
                    annotator.plot_angle_and_count_and_stage(
                        angle_text=state["angle"],  # angle text for display
                        count_text=state["count"],  # count text for workouts
                        stage_text=state["stage"],  # stage position text
                        center_kpt=k[int(self.kpts[1])],  # center keypoint for display
                    )
        plot_im = annotator.result()
        self.display_output(plot_im)  # Display output image, if environment support display

        # Return SolutionResults
        return SolutionResults(
            plot_im=plot_im,
            workout_count=[v["count"] for v in self.states.values()],
            workout_stage=[v["stage"] for v in self.states.values()],
            workout_angle=[v["angle"] for v in self.states.values()],
            total_tracks=len(self.track_ids),
        )