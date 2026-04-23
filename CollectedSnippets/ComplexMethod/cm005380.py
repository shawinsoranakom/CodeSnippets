def get_user_field(
    question: str,
    default_value: str | None = None,
    convert_to: Callable | None = None,
    fallback_message: str | None = None,
) -> Any:
    """
    A utility function that asks a question to the user to get an answer, potentially looping until it gets a valid
    answer.

    Args:
        question (`str`):
            The question to ask the user.
        default_value (`str`, *optional*):
            A potential default value that will be used when the answer is empty.
        convert_to (`Callable`, *optional*):
            If set, the answer will be passed to this function. If this function raises an error on the provided
            answer, the question will be asked again.
        fallback_message (`str`, *optional*):
            A message that will be displayed each time the question is asked again to the user.

    Returns:
        `Any`: The answer provided by the user (or the default), passed through the potential conversion function.
    """
    if not question.endswith(" "):
        question = question + " "
    if default_value is not None:
        question = f"{question} [{default_value}] "

    valid_answer = False
    while not valid_answer:
        answer = input(question)
        if default_value is not None and len(answer) == 0:
            answer = default_value
        if convert_to is not None:
            try:
                answer = convert_to(answer)
                valid_answer = True
            except Exception:
                valid_answer = False
        else:
            valid_answer = True

        if not valid_answer:
            print(fallback_message)

    return answer