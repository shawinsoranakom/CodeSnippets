def resolve_trust_remote_code(
    trust_remote_code, model_name, has_local_code, has_remote_code, error_message=None, upstream_repo=None
):
    """
    Resolves the `trust_remote_code` argument. If there is remote code to be loaded, the user must opt-in to loading
    it.

    Args:
        trust_remote_code (`bool` or `None`):
            User-defined `trust_remote_code` value.
        model_name (`str`):
            The name of the model repository in huggingface.co.
        has_local_code (`bool`):
            Whether the model has local code.
        has_remote_code (`bool`):
            Whether the model has remote code.
        error_message (`str`, *optional*):
            Custom error message to display if there is remote code to load and the user didn't opt-in. If unset, the error
            message will be regarding loading a model with custom code.

    Returns:
        The resolved `trust_remote_code` value.
    """
    if error_message is None:
        if upstream_repo is not None:
            error_message = (
                f"The repository {model_name} references custom code contained in {upstream_repo} which "
                f"must be executed to correctly load the model. You can inspect the repository "
                f"content at https://hf.co/{upstream_repo} .\n"
            )
        elif os.path.isdir(model_name):
            error_message = (
                f"The repository {model_name} contains custom code which must be executed "
                f"to correctly load the model. You can inspect the repository "
                f"content at {os.path.abspath(model_name)} .\n"
            )
        else:
            error_message = (
                f"The repository {model_name} contains custom code which must be executed "
                f"to correctly load the model. You can inspect the repository "
                f"content at https://hf.co/{model_name} .\n"
            )

    if trust_remote_code is None:
        if has_local_code:
            trust_remote_code = False
        elif has_remote_code and TIME_OUT_REMOTE_CODE > 0:
            prev_sig_handler = None
            try:
                prev_sig_handler = signal.signal(signal.SIGALRM, _raise_timeout_error)
                signal.alarm(TIME_OUT_REMOTE_CODE)
                while trust_remote_code is None:
                    answer = input(
                        f"{error_message} You can inspect the repository content at https://hf.co/{model_name}.\n"
                        f"You can avoid this prompt in future by passing the argument `trust_remote_code=True`.\n\n"
                        f"Do you wish to run the custom code? [y/N] "
                    )
                    if answer.lower() in ["yes", "y", "1"]:
                        trust_remote_code = True
                    elif answer.lower() in ["no", "n", "0", ""]:
                        trust_remote_code = False
                signal.alarm(0)
            except Exception:
                # OS which does not support signal.SIGALRM
                raise ValueError(
                    f"{error_message} You can inspect the repository content at https://hf.co/{model_name}.\n"
                    f"Please pass the argument `trust_remote_code=True` to allow custom code to be run."
                )
            finally:
                if prev_sig_handler is not None:
                    signal.signal(signal.SIGALRM, prev_sig_handler)
                    signal.alarm(0)
        elif has_remote_code:
            # For the CI which puts the timeout at 0
            _raise_timeout_error(None, None)

    if has_remote_code and not has_local_code and not trust_remote_code:
        raise ValueError(
            f"{error_message} You can inspect the repository content at https://hf.co/{model_name}.\n"
            f"Please pass the argument `trust_remote_code=True` to allow custom code to be run."
        )

    return trust_remote_code