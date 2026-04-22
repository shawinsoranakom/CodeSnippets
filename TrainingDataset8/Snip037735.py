def save_media_data(
    image_data: Union[bytes, str], mimetype: str, image_id: str
) -> None:
    MEMO_MESSAGE_CALL_STACK.save_image_data(image_data, mimetype, image_id)
    SINGLETON_MESSAGE_CALL_STACK.save_image_data(image_data, mimetype, image_id)