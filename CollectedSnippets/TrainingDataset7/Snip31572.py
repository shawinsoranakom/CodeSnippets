def test_select_related_memory_leak(self):
        self.setup_gc_debug()
        list(Species.objects.select_related("genus"))
        self.assert_no_memory_leaks()