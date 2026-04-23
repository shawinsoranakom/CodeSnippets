def mock_wrapper():
        return MagicMock(side_effect=lambda execute, *args: execute(*args))