def test_iter(self):
        wstate_iter = iter(self.wstates)
        assert next(wstate_iter) == "widget_id_1"
        assert next(wstate_iter) == "widget_id_2"
        with pytest.raises(StopIteration):
            next(wstate_iter)