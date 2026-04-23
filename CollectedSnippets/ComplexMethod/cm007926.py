def test_handler_operations(self):
        director = RequestDirector(logger=FakeLogger())
        handler = FakeRH(logger=FakeLogger())
        director.add_handler(handler)
        assert director.handlers.get(FakeRH.RH_KEY) is handler

        # Handler should overwrite
        handler2 = FakeRH(logger=FakeLogger())
        director.add_handler(handler2)
        assert director.handlers.get(FakeRH.RH_KEY) is not handler
        assert director.handlers.get(FakeRH.RH_KEY) is handler2
        assert len(director.handlers) == 1

        class AnotherFakeRH(FakeRH):
            pass
        director.add_handler(AnotherFakeRH(logger=FakeLogger()))
        assert len(director.handlers) == 2
        assert director.handlers.get(AnotherFakeRH.RH_KEY).RH_KEY == AnotherFakeRH.RH_KEY

        director.handlers.pop(FakeRH.RH_KEY, None)
        assert director.handlers.get(FakeRH.RH_KEY) is None
        assert len(director.handlers) == 1

        # RequestErrors should passthrough
        with pytest.raises(SSLError):
            director.send(Request('ssl://something'))