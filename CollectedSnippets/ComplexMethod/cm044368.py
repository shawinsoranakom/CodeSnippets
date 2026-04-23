def test__check_cache(tensorboardlogs_instance: TensorBoardLogs,
                          mocker: pytest_mock.MockerFixture) -> None:
        """ Test _check_cache works correctly

        Parameters
        ----------
        tensorboadlogs_instance: :class:`lib.gui.analysis.event_reader.TensorBoardLogs`
            The class instance to test
        mocker: :class:`pytest_mock.MockerFixture`
            Mocker for checking _cache_data is called
        """
        is_cached = mocker.patch("lib.gui.analysis.event_reader._Cache.is_cached")
        cache_data = mocker.patch("lib.gui.analysis.event_reader.TensorBoardLogs._cache_data")
        tb_logs = tensorboardlogs_instance

        # Session ID not training
        is_cached.return_value = False
        tb_logs._check_cache(1)
        assert is_cached.called
        assert cache_data.called
        is_cached.reset_mock()
        cache_data.reset_mock()

        is_cached.return_value = True
        tb_logs._check_cache(1)
        assert is_cached.called
        assert not cache_data.called
        is_cached.reset_mock()
        cache_data.reset_mock()

        # Session ID and training
        tb_logs.set_training(True)
        tb_logs._check_cache(1)
        assert not cache_data.called
        cache_data.reset_mock()

        tb_logs._check_cache(2)
        assert cache_data.called
        cache_data.reset_mock()

        # No session id
        tb_logs.set_training(False)
        is_cached.return_value = False

        tb_logs._check_cache(None)
        assert is_cached.called
        assert cache_data.called
        is_cached.reset_mock()
        cache_data.reset_mock()

        is_cached.return_value = True
        tb_logs._check_cache(None)
        assert is_cached.called
        assert not cache_data.called
        is_cached.reset_mock()
        cache_data.reset_mock()