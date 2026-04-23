def test_contenttype_in_separate_db(self):
        ContentType.objects.using("other").all().delete()
        book_other = Book.objects.using("other").create(
            title="Test title other", published=datetime.date(2009, 5, 4)
        )
        book_default = Book.objects.using("default").create(
            title="Test title default", published=datetime.date(2009, 5, 4)
        )
        book_type = ContentType.objects.using("default").get(
            app_label="multiple_database", model="book"
        )

        book = book_type.get_object_for_this_type(title=book_other.title)
        self.assertEqual(book, book_other)
        book = book_type.get_object_for_this_type(using="other", title=book_other.title)
        self.assertEqual(book, book_other)

        with self.assertRaises(Book.DoesNotExist):
            book_type.get_object_for_this_type(title=book_default.title)
        book = book_type.get_object_for_this_type(
            using="default", title=book_default.title
        )
        self.assertEqual(book, book_default)

        all_books = book_type.get_all_objects_for_this_type()
        self.assertCountEqual(all_books, [book_other])