def test_multiple_sort_same_field(self):
        # The changelist displays the correct columns if two columns correspond
        # to the same ordering field.
        dt = datetime.datetime.now()
        p1 = Podcast.objects.create(name="A", release_date=dt)
        p2 = Podcast.objects.create(name="B", release_date=dt - datetime.timedelta(10))
        link1 = reverse("admin:admin_views_podcast_change", args=(quote(p1.pk),))
        link2 = reverse("admin:admin_views_podcast_change", args=(quote(p2.pk),))

        response = self.client.get(reverse("admin:admin_views_podcast_changelist"), {})
        self.assertContentBefore(response, link1, link2)

        p1 = ComplexSortedPerson.objects.create(name="Bob", age=10)
        p2 = ComplexSortedPerson.objects.create(name="Amy", age=20)
        link1 = reverse("admin:admin_views_complexsortedperson_change", args=(p1.pk,))
        link2 = reverse("admin:admin_views_complexsortedperson_change", args=(p2.pk,))

        response = self.client.get(
            reverse("admin:admin_views_complexsortedperson_changelist"), {}
        )
        # Should have 5 columns (including action checkbox col)
        result_list_table_re = re.compile('<table id="result_list">(.*?)</thead>')
        result_list_table_head = result_list_table_re.search(str(response.content))[0]
        self.assertEqual(result_list_table_head.count('<th scope="col"'), 5)

        self.assertContains(response, "Name")
        self.assertContains(response, "Colored name")

        # Check order
        self.assertContentBefore(response, "Name", "Colored name")

        # Check sorting - should be by name
        self.assertContentBefore(response, link2, link1)