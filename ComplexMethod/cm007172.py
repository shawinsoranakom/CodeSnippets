def process_video(self) -> Message:
        """Process video using Pegasus and generate response if message is provided.

        Handles video indexing and question answering using the TwelveLabs API.
        """
        # Check and initialize inputs
        if hasattr(self, "index_id") and self.index_id:
            self._index_id = self.index_id.text if hasattr(self.index_id, "text") else self.index_id

        if hasattr(self, "index_name") and self.index_name:
            self._index_name = self.index_name.text if hasattr(self.index_name, "text") else self.index_name

        if hasattr(self, "video_id") and self.video_id:
            self._video_id = self.video_id.text if hasattr(self.video_id, "text") else self.video_id

        if hasattr(self, "message") and self.message:
            self._message = self.message.text if hasattr(self.message, "text") else self.message

        try:
            # If we have a message and already processed video, use existing video_id
            if self._message and self._video_id and self._video_id != "":
                self.status = f"Have video id: {self._video_id}"

                client = TwelveLabs(api_key=self.api_key)

                self.status = f"Processing query (w/ video ID): {self._video_id} {self._message}"
                self.log(self.status)

                response = client.generate.text(
                    video_id=self._video_id,
                    prompt=self._message,
                    temperature=self.temperature,
                )
                return Message(text=response.data)

            # Otherwise process new video
            if not self.videodata or not isinstance(self.videodata, list) or len(self.videodata) != 1:
                return Message(text="Please provide exactly one video")

            video_path = self.videodata[0].data.get("text")
            if not video_path or not Path(video_path).exists():
                return Message(text="Invalid video path")

            if not self.api_key:
                return Message(text="No API key provided")

            client = TwelveLabs(api_key=self.api_key)

            # Get or create index
            try:
                index_id, index_name = self._get_or_create_index(client)
                self.status = f"Using index: {index_name} (ID: {index_id})"
                self.log(f"Using index: {index_name} (ID: {index_id})")
                self._index_id = index_id
                self._index_name = index_name
            except IndexCreationError as e:
                return Message(text=f"Failed to get/create index: {e}")

            with Path(video_path).open("rb") as video_file:
                task = client.task.create(index_id=self._index_id, file=video_file)
            self._task_id = task.id

            # Wait for processing to complete
            task.wait_for_done(sleep_interval=5, callback=self.on_task_update)

            if task.status != "ready":
                return Message(text=f"Processing failed with status {task.status}")

            # Store video_id for future use
            self._video_id = task.video_id

            # Generate response if message provided
            if self._message:
                self.status = f"Processing query: {self._message}"
                self.log(self.status)

                response = client.generate.text(
                    video_id=self._video_id,
                    prompt=self._message,
                    temperature=self.temperature,
                )
                return Message(text=response.data)

            success_msg = (
                f"Video processed successfully. You can now ask questions about the video. Video ID: {self._video_id}"
            )
            return Message(text=success_msg)

        except (ValueError, KeyError, IndexCreationError, TaskError, TaskTimeoutError) as e:
            self.log(f"Error: {e!s}", "ERROR")
            # Clear stored IDs on error
            self._video_id = None
            self._index_id = None
            self._task_id = None
            return Message(text=f"Error: {e!s}")