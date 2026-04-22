def save_image_data(
        self, image_data: Union[bytes, str], mimetype: str, image_id: str
    ) -> None:
        self._media_data.append(MediaMsgData(image_data, mimetype, image_id))