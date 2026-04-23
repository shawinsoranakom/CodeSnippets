def test_cull_nonexistent(self):
        self.wstates.cull_nonexistent({"widget_id_1"})
        assert "widget_id_1" in self.wstates
        assert "widget_id_2" not in self.wstates