def test_bug(self):
        prefetcher = get_prefetcher(self.rooms[0], "house", "house")[0]
        queryset = prefetcher.get_prefetch_querysets(list(Room.objects.all()))[0]
        self.assertNotIn(" JOIN ", str(queryset.query))