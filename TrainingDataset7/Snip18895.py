def test_saving_an_object_again_does_not_create_a_new_object(self):
        a = Article(headline="original", pub_date=datetime(2014, 5, 16))
        a.save()
        current_id = a.id

        a.save()
        self.assertEqual(a.id, current_id)

        a.headline = "Updated headline"
        a.save()
        self.assertEqual(a.id, current_id)