def test_bug(self):
        list(
            WordEntry.objects.prefetch_related(
                "lesson_entry", "lesson_entry__wordentry_set"
            )
        )