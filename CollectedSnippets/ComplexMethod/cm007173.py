def process_video(self, video_path: str, clip_duration: int, *, include_original: bool) -> list[Data]:
        """Process video and split it into clips using FFmpeg."""
        try:
            # Get video duration
            total_duration = self.get_video_duration(video_path)

            # Calculate number of clips (ceiling to include partial clip)
            num_clips = math.ceil(total_duration / clip_duration)
            self.log(
                f"Total duration: {total_duration}s, Clip duration: {clip_duration}s, Number of clips: {num_clips}"
            )

            # Create output directory for clips
            output_dir = self.get_output_dir(video_path)

            # Get original video info
            path_obj = Path(video_path)
            original_filename = path_obj.name
            original_name = path_obj.stem

            # List to store all video paths (including original if requested)
            video_paths: list[Data] = []

            # Add original video if requested
            if include_original:
                original_data: dict[str, Any] = {
                    "text": video_path,
                    "metadata": {
                        "source": video_path,
                        "type": "video",
                        "clip_index": -1,  # -1 indicates original video
                        "duration": int(total_duration),  # Convert to int
                        "original_video": {
                            "name": original_name,
                            "filename": original_filename,
                            "path": video_path,
                            "duration": int(total_duration),  # Convert to int
                            "total_clips": int(num_clips),
                            "clip_duration": int(clip_duration),
                        },
                    },
                }
                video_paths.append(Data(data=original_data))

            # Split video into clips
            for i in range(int(num_clips)):  # Convert num_clips to int for range
                start_time = float(i * clip_duration)  # Convert to float for time calculations
                end_time = min(float((i + 1) * clip_duration), total_duration)
                duration = end_time - start_time

                # Handle last clip if it's shorter
                if i == int(num_clips) - 1 and duration < clip_duration:  # Convert num_clips to int for comparison
                    if self.last_clip_handling == "Truncate":
                        # Skip if the last clip would be too short
                        continue
                    if self.last_clip_handling == "Overlap Previous" and i > 0:
                        # Start from earlier to make full duration
                        start_time = total_duration - clip_duration
                        duration = clip_duration
                    # For "Keep Short", we use the original start_time and duration

                # Skip if duration is too small (less than 1 second)
                if duration < 1:
                    continue

                # Generate output path
                output_path = Path(output_dir) / f"clip_{i:03d}.mp4"
                output_path_str = str(output_path)

                try:
                    # Use FFmpeg to split the video
                    cmd = [
                        "ffmpeg",
                        "-i",
                        video_path,
                        "-ss",
                        str(start_time),
                        "-t",
                        str(duration),
                        "-c:v",
                        "libx264",
                        "-c:a",
                        "aac",
                        "-y",  # Overwrite output file if it exists
                        output_path_str,
                    ]

                    result = subprocess.run(  # noqa: S603
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        shell=False,  # Explicitly set shell=False for security
                    )
                    if result.returncode != 0:
                        error_msg = f"FFmpeg error: {result.stderr}"
                        raise RuntimeError(error_msg)

                    # Create timestamp string for metadata
                    start_min = int(start_time // 60)
                    start_sec = int(start_time % 60)
                    end_min = int(end_time // 60)
                    end_sec = int(end_time % 60)
                    timestamp_str = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

                    # Create Data object for the clip
                    clip_data: dict[str, Any] = {
                        "text": output_path_str,
                        "metadata": {
                            "source": video_path,
                            "type": "video",
                            "clip_index": i,
                            "start_time": float(start_time),
                            "end_time": float(end_time),
                            "duration": float(duration),
                            "original_video": {
                                "name": original_name,
                                "filename": original_filename,
                                "path": video_path,
                                "duration": int(total_duration),
                                "total_clips": int(num_clips),
                                "clip_duration": int(clip_duration),
                            },
                            "clip": {
                                "index": i,
                                "total": int(num_clips),
                                "duration": float(duration),
                                "start_time": float(start_time),
                                "end_time": float(end_time),
                                "timestamp": timestamp_str,
                            },
                        },
                    }
                    video_paths.append(Data(data=clip_data))

                except Exception as e:
                    self.log(f"Error processing clip {i}: {e!s}", "ERROR")
                    raise

            self.log(f"Created {len(video_paths)} clips in {output_dir}")
        except Exception as e:
            self.log(f"Error processing video: {e!s}", "ERROR")
            raise
        else:
            return video_paths