def test_emptylistfieldfilter_genericrelation(self):
        class BookmarkGenericRelation(ModelAdmin):
            list_filter = (("tags", EmptyFieldListFilter),)

        modeladmin = BookmarkGenericRelation(Bookmark, site)

        django_bookmark = Bookmark.objects.create(url="https://www.djangoproject.com/")
        python_bookmark = Bookmark.objects.create(url="https://www.python.org/")
        none_tags = Bookmark.objects.create(url="https://www.kernel.org/")
        TaggedItem.objects.create(content_object=django_bookmark, tag="python")
        TaggedItem.objects.create(content_object=python_bookmark, tag="python")

        tests = [
            ({"tags__isempty": "1"}, [none_tags]),
            ({"tags__isempty": "0"}, [django_bookmark, python_bookmark]),
        ]
        for query_string, expected_result in tests:
            with self.subTest(query_string=query_string):
                request = self.request_factory.get("/", query_string)
                request.user = self.alfred
                changelist = modeladmin.get_changelist_instance(request)
                queryset = changelist.get_queryset(request)
                self.assertCountEqual(queryset, expected_result)