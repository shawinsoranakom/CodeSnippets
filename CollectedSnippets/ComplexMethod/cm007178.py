def load_files(self) -> DataFrame:
        """Load video files and return a list of Data objects."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)

        try:
            self.log("DEBUG: Starting video file load")
            if not hasattr(self, "file_path") or not self.file_path:
                self.log("DEBUG: No video file path provided")
                return DataFrame()

            self.log(f"DEBUG: Loading video from path: {self.file_path}")

            # Verify file exists
            file_path_obj = Path(self.file_path)
            if not file_path_obj.exists():
                self.log(f"DEBUG: Video file not found at path: {self.file_path}")
                return DataFrame()

            # Verify file size
            file_size = file_path_obj.stat().st_size
            self.log(f"DEBUG: Video file size: {file_size} bytes")

            # Create a proper Data object with the video path
            video_data = {
                "text": self.file_path,
                "metadata": {"source": self.file_path, "type": "video", "size": file_size},
            }

            self.log(f"DEBUG: Created video data: {video_data}")
            result = DataFrame(data=[video_data])

            # Log the result to verify it's a proper Data object
            self.log("DEBUG: Returning list with Data objects")
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.log(f"DEBUG: File error in video load_files: {e!s}", "ERROR")
            return DataFrame()
        except ImportError as e:
            self.log(f"DEBUG: Import error in video load_files: {e!s}", "ERROR")
            return DataFrame()
        except (ValueError, TypeError) as e:
            self.log(f"DEBUG: Value or type error in video load_files: {e!s}", "ERROR")
            return DataFrame()
        else:
            return result