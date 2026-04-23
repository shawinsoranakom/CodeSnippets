def inner(test_func):
        def wrapper(*args):
            class mock_getpass:
                @staticmethod
                def getpass(prompt=b"Password: ", stream=None):
                    if callable(inputs["password"]):
                        return inputs["password"]()
                    return inputs["password"]

            def mock_input(prompt):
                assert "__proxy__" not in prompt
                response = None
                for key, val in inputs.items():
                    if val == "KeyboardInterrupt":
                        raise KeyboardInterrupt
                    # get() fallback because sometimes 'key' is the actual
                    # prompt rather than a shortcut name.
                    prompt_msgs = MOCK_INPUT_KEY_TO_PROMPTS.get(key, key)
                    if isinstance(prompt_msgs, list):
                        prompt_msgs = [
                            msg() if callable(msg) else msg for msg in prompt_msgs
                        ]
                    if prompt in prompt_msgs:
                        if callable(val):
                            response = val()
                        else:
                            response = val
                        break
                if response is None:
                    raise ValueError("Mock input for %r not found." % prompt)
                return response

            old_getpass = createsuperuser.getpass
            old_input = builtins.input
            createsuperuser.getpass = mock_getpass
            builtins.input = mock_input
            try:
                test_func(*args)
            finally:
                createsuperuser.getpass = old_getpass
                builtins.input = old_input

        return wrapper