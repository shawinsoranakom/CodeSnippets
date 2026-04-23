def _build_duplicate_form_message(user_key: Optional[str] = None) -> str:
    if user_key is not None:
        message = textwrap.dedent(
            f"""
            There are multiple identical forms with `key='{user_key}'`.

            To fix this, please make sure that the `key` argument is unique for
            each `st.form` you create.
            """
        )
    else:
        message = textwrap.dedent(
            """
            There are multiple identical forms with the same generated key.

            When a form is created, it's assigned an internal key based on
            its structure. Multiple forms with an identical structure will
            result in the same internal key, which causes this error.

            To fix this error, please pass a unique `key` argument to
            `st.form`.
            """
        )

    return message.strip("\n")