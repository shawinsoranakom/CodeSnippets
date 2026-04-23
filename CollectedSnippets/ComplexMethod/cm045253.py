def __empty_content_to_whitespace(
    content: Union[str, List[Union[str, Image]]],
) -> Union[str, Iterable[Any]]:
    if isinstance(content, str) and not content.strip():
        return " "
    elif isinstance(content, list) and not any(isinstance(x, str) and not x.strip() for x in content):
        for idx, message in enumerate(content):
            if isinstance(message, str) and not message.strip():
                content[idx] = " "

    return content