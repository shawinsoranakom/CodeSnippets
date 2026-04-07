def test_pk(self):
        query = Query(User)
        path, final_field, targets, rest = query.names_to_path(["pk"], User._meta)

        self.assertEqual(path, [])
        self.assertEqual(final_field, User._meta.get_field("pk"))
        self.assertEqual(targets, (User._meta.get_field("pk"),))
        self.assertEqual(rest, [])