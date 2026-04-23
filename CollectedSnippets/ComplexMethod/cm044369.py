def test_cache_events(self,
                          event_parser_instance: _EventParser,
                          mocker: pytest_mock.MockerFixture,
                          monkeypatch: pytest.MonkeyPatch) -> None:
        """ Test cache_events works correctly

        Parameters
        ----------
        event_parser_instance: :class:`lib.gui.analysis.event_reader._EventParser`
            The class instance to test
        mocker: :class:`pytest_mock.MockerFixture`
            Mocker for capturing method calls
        monkeypatch: :class:`pytest.MonkeyPatch`
            For patching different iterators for testing output
        """
        monkeypatch.setattr("lib.utils._FS_BACKEND", "cpu")

        event_parse = event_parser_instance
        event_parse._parse_outputs = T.cast(MagicMock, mocker.MagicMock())  # type:ignore
        event_parse._process_event = T.cast(MagicMock, mocker.MagicMock())  # type:ignore
        event_parse._cache.cache_data = T.cast(MagicMock, mocker.MagicMock())  # type:ignore

        # keras model
        monkeypatch.setattr(event_parse,
                            "_iterator",
                            iter([self._create_example_event(0, 1., time())]))
        event_parse.cache_events(1)
        assert event_parse._parse_outputs.called
        assert not event_parse._process_event.called
        assert event_parse._cache.cache_data.called
        event_parse._parse_outputs.reset_mock()
        event_parse._process_event.reset_mock()
        event_parse._cache.cache_data.reset_mock()

        # Batch item
        monkeypatch.setattr(event_parse,
                            "_iterator",
                            iter([self._create_example_event(1, 1., time())]))
        event_parse.cache_events(1)
        assert not event_parse._parse_outputs.called
        assert event_parse._process_event.called
        assert event_parse._cache.cache_data.called
        event_parse._parse_outputs.reset_mock()
        event_parse._process_event.reset_mock()
        event_parse._cache.cache_data.reset_mock()

        # No summary value
        monkeypatch.setattr(event_parse,
                            "_iterator",
                            iter([event_pb2.Event(step=1).SerializeToString()]))
        assert not event_parse._parse_outputs.called
        assert not event_parse._process_event.called
        assert not event_parse._cache.cache_data.called
        event_parse._parse_outputs.reset_mock()
        event_parse._process_event.reset_mock()
        event_parse._cache.cache_data.reset_mock()