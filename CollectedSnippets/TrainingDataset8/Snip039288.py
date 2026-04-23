def get_text_or_block(delta):
    if delta.WhichOneof("type") == "new_element":
        element = delta.new_element
        if element.WhichOneof("type") == "text":
            return element.text.body
    elif delta.WhichOneof("type") == "add_block":
        return "new_block"