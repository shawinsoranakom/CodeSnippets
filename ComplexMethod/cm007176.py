def index_videos(self) -> list[Data]:
        """Indexes each video and adds the video_id to its metadata."""
        if not self.videodata:
            self.status = "No video data provided."
            return []

        if not self.api_key:
            error_msg = "TwelveLabs API Key is required"
            raise IndexCreationError(error_msg)

        if not (hasattr(self, "index_name") and self.index_name) and not (hasattr(self, "index_id") and self.index_id):
            error_msg = "Either index_name or index_id must be provided"
            raise IndexCreationError(error_msg)

        client = TwelveLabs(api_key=self.api_key)
        indexed_data_list: list[Data] = []

        # Get or create the index
        try:
            index_id, index_name = self._get_or_create_index(client)
            self.status = f"Using index: {index_name} (ID: {index_id})"
        except IndexCreationError as e:
            self.status = f"Failed to get/create TwelveLabs index: {e!s}"
            raise

        # First, validate all videos and create a list of valid ones
        valid_videos: list[tuple[Data, str]] = []
        for video_data_item in self.videodata:
            if not isinstance(video_data_item, Data):
                self.status = f"Skipping invalid data item: {video_data_item}"
                continue

            video_info = video_data_item.data
            if not isinstance(video_info, dict):
                self.status = f"Skipping item with invalid data structure: {video_info}"
                continue

            video_path = video_info.get("text")
            if not video_path or not isinstance(video_path, str):
                self.status = f"Skipping item with missing or invalid video path: {video_info}"
                continue

            if not Path(video_path).exists():
                self.status = f"Video file not found, skipping: {video_path}"
                continue

            valid_videos.append((video_data_item, video_path))

        if not valid_videos:
            self.status = "No valid videos to process."
            return []

        # Upload all videos first and collect their task IDs
        upload_tasks: list[tuple[Data, str, str]] = []  # (data_item, video_path, task_id)
        for data_item, video_path in valid_videos:
            try:
                task_id = self._upload_video(client, video_path, index_id)
                upload_tasks.append((data_item, video_path, task_id))
            except (ValueError, KeyError) as e:
                self.status = f"Failed to upload {video_path}: {e!s}"
                continue

        # Now check all tasks in parallel using a thread pool
        with ThreadPoolExecutor(max_workers=min(10, len(upload_tasks))) as executor:
            futures = []
            for data_item, video_path, task_id in upload_tasks:
                future = executor.submit(self._wait_for_task_completion, client, task_id, video_path)
                futures.append((data_item, video_path, future))

            # Process results as they complete
            for data_item, video_path, future in futures:
                try:
                    completed_task = future.result()
                    if completed_task.status == "ready":
                        video_id = completed_task.video_id
                        video_name = Path(video_path).name
                        self.status = f"Video {video_name} indexed successfully. Video ID: {video_id}"

                        # Add video_id to the metadata
                        video_info = data_item.data
                        if "metadata" not in video_info:
                            video_info["metadata"] = {}
                        elif not isinstance(video_info["metadata"], dict):
                            self.status = f"Warning: Overwriting non-dict metadata for {video_path}"
                            video_info["metadata"] = {}

                        video_info["metadata"].update(
                            {"video_id": video_id, "index_id": index_id, "index_name": index_name}
                        )

                        updated_data_item = Data(data=video_info)
                        indexed_data_list.append(updated_data_item)
                except (TaskError, TaskTimeoutError) as e:
                    self.status = f"Failed to process {video_path}: {e!s}"

        if not indexed_data_list:
            self.status = "No videos were successfully indexed."
        else:
            self.status = f"Finished indexing {len(indexed_data_list)}/{len(self.videodata)} videos."

        return indexed_data_list