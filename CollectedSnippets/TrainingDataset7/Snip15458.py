def test_emptylistfieldfilter(self):
        empty_description = Department.objects.create(code="EMPT", description="")
        none_description = Department.objects.create(code="NONE", description=None)
        empty_title = Book.objects.create(title="", author=self.alfred)

        department_admin = DepartmentAdminWithEmptyFieldListFilter(Department, site)
        book_admin = BookAdminWithEmptyFieldListFilter(Book, site)

        tests = [
            # Allows nulls and empty strings.
            (
                department_admin,
                {"description__isempty": "1"},
                [empty_description, none_description],
            ),
            (
                department_admin,
                {"description__isempty": "0"},
                [self.dev, self.design],
            ),
            # Allows nulls.
            (book_admin, {"author__isempty": "1"}, [self.guitar_book]),
            (
                book_admin,
                {"author__isempty": "0"},
                [self.django_book, self.bio_book, self.djangonaut_book, empty_title],
            ),
            # Allows empty strings.
            (book_admin, {"title__isempty": "1"}, [empty_title]),
            (
                book_admin,
                {"title__isempty": "0"},
                [
                    self.django_book,
                    self.bio_book,
                    self.djangonaut_book,
                    self.guitar_book,
                ],
            ),
        ]
        for modeladmin, query_string, expected_result in tests:
            with self.subTest(
                modeladmin=modeladmin.__class__.__name__,
                query_string=query_string,
            ):
                request = self.request_factory.get("/", query_string)
                request.user = self.alfred
                changelist = modeladmin.get_changelist_instance(request)
                queryset = changelist.get_queryset(request)
                self.assertCountEqual(queryset, expected_result)