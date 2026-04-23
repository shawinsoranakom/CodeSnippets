async def get_data_side_effect(*_args, **_kwargs):
            """Return data based on the mocked Hole instance state."""
            if wrong_host:
                raise HoleConnectionError("Cannot fetch data from Pi-hole: err")
            password = getattr(mocked_hole, "password", None)
            api_token = getattr(mocked_hole, "api_token", None)
            if (
                raise_exception
                or incorrect_app_password
                or (api_version == 5 and (not api_token or api_token == "wrong_token"))
                or (api_version == 6 and password not in ["newkey", "apikey"])
            ):
                mocked_hole.data = [] if api_version == 5 else {}
            elif password in ["newkey", "apikey"] or api_token in ["newkey", "apikey"]:
                mocked_hole.data = ZERO_DATA_V6 if api_version == 6 else ZERO_DATA