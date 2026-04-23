def _parse_video_data(
        self,
        data: ModalityData[VideoItem],
    ) -> ModalityDataItems[Any, Any] | None:
        if data is None:
            return None

        if self.is_embeddings(data):
            return VideoEmbeddingItems(data, self.expected_hidden_size)

        data_items: list[VideoItem]
        if (is_list_of(data, PILImage.Image) and len(data) > 0) or (
            isinstance(data, (np.ndarray, torch.Tensor)) and data.ndim == 4
        ):
            data_items = [data]
        elif isinstance(data, (np.ndarray, torch.Tensor)):
            data_items = [elem for elem in data]
        elif isinstance(data, tuple) and len(data) == 2:
            data_items = [data]
        else:
            data_items = data  # type: ignore[assignment]

        new_videos = list[tuple[np.ndarray, dict[str, Any] | None]]()
        metadata_lst: list[dict[str, Any] | None] = []
        for data_item in data_items:
            video, metadata = self._get_video_with_metadata(data_item)
            if self.video_needs_metadata:
                if metadata is None:
                    raise ValueError(
                        "Video metadata is required but not found in mm input. "
                        "Please check your video input in `multi_modal_data`"
                    )
                new_videos.append((video, metadata))
                metadata_lst.append(metadata)
            else:
                new_videos.append(video)

        if not self.video_needs_metadata:
            metadata = None

        return VideoProcessorItems(new_videos, metadata=metadata_lst)