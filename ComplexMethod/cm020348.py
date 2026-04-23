def make_mock(**kwargs: Any) -> MagicMock:
        mocked_hole = MagicMock()
        # Set constructor kwargs as attributes
        for key, value in kwargs.items():
            setattr(mocked_hole, key, value)

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

        async def ftl_side_effect():
            mocked_hole.data = FTL_ERROR

        mocked_hole.authenticate = AsyncMock(side_effect=authenticate_side_effect)
        mocked_hole.get_data = AsyncMock(side_effect=get_data_side_effect)

        if ftl_error:
            # two unauthenticated instances are created in `determine_api_version` before aync_try_connect is called
            if len(instances) > 1:
                mocked_hole.get_data = AsyncMock(side_effect=ftl_side_effect)
        mocked_hole.get_versions = AsyncMock(return_value=None)
        mocked_hole.enable = AsyncMock()
        mocked_hole.disable = AsyncMock()

        # Set versions and version properties
        if has_versions:
            versions = (
                SAMPLE_VERSIONS_WITH_UPDATES
                if has_update
                else SAMPLE_VERSIONS_NO_UPDATES
            )
            mocked_hole.versions = versions
            mocked_hole.ftl_current = versions["FTL_current"]
            mocked_hole.ftl_latest = versions["FTL_latest"]
            mocked_hole.ftl_update = versions["FTL_update"]
            mocked_hole.core_current = versions["core_current"]
            mocked_hole.core_latest = versions["core_latest"]
            mocked_hole.core_update = versions["core_update"]
            mocked_hole.web_current = versions["web_current"]
            mocked_hole.web_latest = versions["web_latest"]
            mocked_hole.web_update = versions["web_update"]
        else:
            mocked_hole.versions = None

        # Set initial data
        if has_data:
            mocked_hole.data = ZERO_DATA_V6 if api_version == 6 else ZERO_DATA
        else:
            mocked_hole.data = [] if api_version == 5 else {}
        instances.append(mocked_hole)
        return mocked_hole