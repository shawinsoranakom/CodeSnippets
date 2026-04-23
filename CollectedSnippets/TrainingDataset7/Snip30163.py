def test_overriding_prefetch(self):
        with self.assertNumQueries(3):
            qs = Author.objects.prefetch_related("books", "books__read_by")
            lists = [
                [[str(r) for r in b.read_by.all()] for b in a.books.all()] for a in qs
            ]
            self.assertEqual(
                lists,
                [
                    [["Amy"], ["Belinda"]],  # Charlotte - Poems, Jane Eyre
                    [["Amy"]],  # Anne - Poems
                    [["Amy"], []],  # Emily - Poems, Wuthering Heights
                    [["Amy", "Belinda"]],  # Jane - Sense and Sense
                ],
            )
        with self.assertNumQueries(3):
            qs = Author.objects.prefetch_related("books__read_by", "books")
            lists = [
                [[str(r) for r in b.read_by.all()] for b in a.books.all()] for a in qs
            ]
            self.assertEqual(
                lists,
                [
                    [["Amy"], ["Belinda"]],  # Charlotte - Poems, Jane Eyre
                    [["Amy"]],  # Anne - Poems
                    [["Amy"], []],  # Emily - Poems, Wuthering Heights
                    [["Amy", "Belinda"]],  # Jane - Sense and Sense
                ],
            )