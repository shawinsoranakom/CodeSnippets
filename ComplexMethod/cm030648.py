def _test_queue(cls, obj):
        assert obj.qsize() == 2
        assert obj.full()
        assert not obj.empty()
        assert obj.get() == 5
        assert not obj.empty()
        assert obj.get() == 6
        assert obj.empty()