def test_reverse_join_trimming(self):
        qs = Author.objects.annotate(Count("book_contact_set__contact"))
        self.assertIn(" JOIN ", str(qs.query))