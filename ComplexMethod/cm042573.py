def test_collector(self, crawler: Crawler) -> None:
        stats = StatsCollector(crawler)
        assert stats.get_stats() == {}
        assert stats.get_value("anything") is None
        assert stats.get_value("anything", "default") == "default"
        stats.set_value("test", "value")
        assert stats.get_stats() == {"test": "value"}
        stats.set_value("test2", 23)
        assert stats.get_stats() == {"test": "value", "test2": 23}
        assert stats.get_value("test2") == 23
        stats.inc_value("test2")
        assert stats.get_value("test2") == 24
        stats.inc_value("test2", 6)
        assert stats.get_value("test2") == 30
        stats.max_value("test2", 6)
        assert stats.get_value("test2") == 30
        stats.max_value("test2", 40)
        assert stats.get_value("test2") == 40
        stats.max_value("test3", 1)
        assert stats.get_value("test3") == 1
        stats.min_value("test2", 60)
        assert stats.get_value("test2") == 40
        stats.min_value("test2", 35)
        assert stats.get_value("test2") == 35
        stats.min_value("test4", 7)
        assert stats.get_value("test4") == 7