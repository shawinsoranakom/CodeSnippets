def patch_app_session(self):
        """Mock the Runtime's AppSession import. Use this on tests where we don't want
        actual sessions to be instantiated, or scripts to be run.
        """
        return mock.patch(
            "streamlit.runtime.runtime.AppSession",
            # new_callable must return a function, not an object, or else
            # there will only be a single AppSession mock. Hence the lambda.
            new_callable=lambda: self._create_mock_app_session,
        )