def setUpTestData(cls):
        LessonEntry.objects.bulk_create(
            LessonEntry(id=id_, name1=name1, name2=name2)
            for id_, name1, name2 in [
                (1, "einfach", "simple"),
                (2, "schwierig", "difficult"),
            ]
        )
        WordEntry.objects.bulk_create(
            WordEntry(id=id_, lesson_entry_id=lesson_entry_id, name=name)
            for id_, lesson_entry_id, name in [
                (1, 1, "einfach"),
                (2, 1, "simple"),
                (3, 2, "schwierig"),
                (4, 2, "difficult"),
            ]
        )