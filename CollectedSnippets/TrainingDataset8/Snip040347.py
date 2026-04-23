def _patch_app_session(self):
        """Mock the Server's AppSession import. We don't want
        actual sessions to be instantiated, or scripts to be run.
        """

        return mock.patch(
            "streamlit.runtime.runtime.AppSession",
            # new_callable must return a function, not an object, or else
            # there will only be a single AppSession mock. Hence the lambda.
            new_callable=lambda: self._create_mock_app_session,
        )