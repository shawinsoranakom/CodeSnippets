def process(self) -> list[Data]:
        """Process the input video and return a list of Data objects containing the clips."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)

        try:
            # Get the input video path from the previous component
            if not hasattr(self, "videodata") or not isinstance(self.videodata, list) or len(self.videodata) != 1:
                error_msg = "Please provide exactly one video"
                raise ValueError(error_msg)

            video_path = self.videodata[0].data.get("text")
            if not video_path or not Path(video_path).exists():
                error_msg = "Invalid video path"
                raise ValueError(error_msg)

            # Validate video path to prevent shell injection
            if not isinstance(video_path, str) or any(c in video_path for c in ";&|`$(){}[]<>*?!#~"):
                error_msg = "Invalid video path contains unsafe characters"
                raise ValueError(error_msg)

            # Process the video
            return self.process_video(video_path, self.clip_duration, include_original=self.include_original)

        except Exception as e:
            self.log(f"Error in split video component: {e!s}", "ERROR")
            raise