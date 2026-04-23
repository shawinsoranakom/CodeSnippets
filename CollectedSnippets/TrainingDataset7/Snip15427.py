def test_listfilter_genericrelation(self):
        django_bookmark = Bookmark.objects.create(url="https://www.djangoproject.com/")
        python_bookmark = Bookmark.objects.create(url="https://www.python.org/")
        kernel_bookmark = Bookmark.objects.create(url="https://www.kernel.org/")

        TaggedItem.objects.create(content_object=django_bookmark, tag="python")
        TaggedItem.objects.create(content_object=python_bookmark, tag="python")
        TaggedItem.objects.create(content_object=kernel_bookmark, tag="linux")

        modeladmin = BookmarkAdminGenericRelation(Bookmark, site)

        request = self.request_factory.get("/", {"tags__tag": "python"})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)

        expected = [python_bookmark, django_bookmark]
        self.assertEqual(list(queryset), expected)