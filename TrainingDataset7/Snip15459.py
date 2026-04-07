def test_emptylistfieldfilter_reverse_relationships(self):
        class UserAdminReverseRelationship(UserAdmin):
            list_filter = (("books_contributed", EmptyFieldListFilter),)

        ImprovedBook.objects.create(book=self.guitar_book)
        no_employees = Department.objects.create(code="NONE", description=None)

        book_admin = BookAdminWithEmptyFieldListFilter(Book, site)
        department_admin = DepartmentAdminWithEmptyFieldListFilter(Department, site)
        user_admin = UserAdminReverseRelationship(User, site)

        tests = [
            # Reverse one-to-one relationship.
            (
                book_admin,
                {"improvedbook__isempty": "1"},
                [self.django_book, self.bio_book, self.djangonaut_book],
            ),
            (book_admin, {"improvedbook__isempty": "0"}, [self.guitar_book]),
            # Reverse foreign key relationship.
            (department_admin, {"employee__isempty": "1"}, [no_employees]),
            (department_admin, {"employee__isempty": "0"}, [self.dev, self.design]),
            # Reverse many-to-many relationship.
            (user_admin, {"books_contributed__isempty": "1"}, [self.alfred]),
            (user_admin, {"books_contributed__isempty": "0"}, [self.bob, self.lisa]),
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