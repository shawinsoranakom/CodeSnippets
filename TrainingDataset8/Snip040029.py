def test_get_stats(self):
        """StatsManager.get_stats should return all providers' stats."""
        manager = StatsManager()
        provider1 = MockStatsProvider()
        provider2 = MockStatsProvider()
        manager.register_provider(provider1)
        manager.register_provider(provider2)

        # No stats
        self.assertEqual([], manager.get_stats())

        # Some stats
        provider1.stats = [
            CacheStat("provider1", "foo", 1),
            CacheStat("provider1", "bar", 2),
        ]

        provider2.stats = [
            CacheStat("provider2", "baz", 3),
            CacheStat("provider2", "qux", 4),
        ]

        self.assertEqual(provider1.stats + provider2.stats, manager.get_stats())