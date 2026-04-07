def test_related_manager(self):
        "Related managers return managers, not querysets"
        mark = Person.objects.using("other").create(name="Mark Pilgrim")

        # extra_arg is removed by the BookManager's implementation of
        # create(); but the BookManager's implementation won't get called
        # unless edited returns a Manager, not a queryset
        mark.book_set.create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
            extra_arg=True,
        )
        mark.book_set.get_or_create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
            extra_arg=True,
        )
        mark.edited.create(
            title="Dive into Water", published=datetime.date(2009, 5, 4), extra_arg=True
        )
        mark.edited.get_or_create(
            title="Dive into Water", published=datetime.date(2009, 5, 4), extra_arg=True
        )