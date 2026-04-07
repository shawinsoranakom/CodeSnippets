def test_id(self):
        query = Query(User)
        path, final_field, targets, rest = query.names_to_path(["id"], User._meta)

        self.assertEqual(path, [])
        self.assertEqual(final_field, User._meta.get_field("id"))
        self.assertEqual(targets, (User._meta.get_field("id"),))
        self.assertEqual(rest, [])