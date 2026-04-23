async def authenticate_side_effect(*_args, **_kwargs):
            if wrong_host:
                raise HoleConnectionError("Cannot authenticate with Pi-hole: err")
            password = getattr(mocked_hole, "password", None)

            if (
                raise_exception
                or incorrect_app_password
                or api_version == 5
                or (api_version == 6 and password not in ["newkey", "apikey"])
            ):
                if api_version == 6 and (
                    incorrect_app_password or password not in ["newkey", "apikey"]
                ):
                    raise HoleError("Authentication failed: Invalid password")
                raise HoleConnectionError