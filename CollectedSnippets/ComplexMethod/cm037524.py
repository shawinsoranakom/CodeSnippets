def _parse_image_data(
        self,
        data: ModalityData[ImageItem],
    ) -> ModalityDataItems[Any, Any] | None:
        if data is None:
            return None

        if self.is_embeddings(data):
            return ImageEmbeddingItems(data, self.expected_hidden_size)

        if isinstance(data, (PILImage.Image, MediaWithBytes)) or (
            isinstance(data, (np.ndarray, torch.Tensor)) and data.ndim == 3
        ):
            data_items = [data]
        elif isinstance(data, (np.ndarray, torch.Tensor)):
            data_items = [elem for elem in data]
        else:
            data_items = data

        return ImageProcessorItems(data_items)