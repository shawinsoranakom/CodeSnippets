def getpass(prompt=b"Password: ", stream=None):
                    if callable(inputs["password"]):
                        return inputs["password"]()
                    return inputs["password"]