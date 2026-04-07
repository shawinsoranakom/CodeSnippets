def test_assert_num_queries_with_client(self):
        person = Person.objects.create(name="test")

        self.assertNumQueries(
            1, self.client.get, "/test_utils/get_person/%s/" % person.pk
        )

        self.assertNumQueries(
            1, self.client.get, "/test_utils/get_person/%s/" % person.pk
        )

        def test_func():
            self.client.get("/test_utils/get_person/%s/" % person.pk)
            self.client.get("/test_utils/get_person/%s/" % person.pk)

        self.assertNumQueries(2, test_func)