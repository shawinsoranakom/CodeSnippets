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