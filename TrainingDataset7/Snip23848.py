def test_explicitly_ordered_list_view(self):
        Book.objects.create(
            name="Zebras for Dummies", pages=800, pubdate=datetime.date(2006, 9, 1)
        )
        res = self.client.get("/list/books/sorted/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object_list"][0].name, "2066")
        self.assertEqual(res.context["object_list"][1].name, "Dreaming in Code")
        self.assertEqual(res.context["object_list"][2].name, "Zebras for Dummies")

        res = self.client.get("/list/books/sortedbypagesandnamedec/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object_list"][0].name, "Dreaming in Code")
        self.assertEqual(res.context["object_list"][1].name, "Zebras for Dummies")
        self.assertEqual(res.context["object_list"][2].name, "2066")