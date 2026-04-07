def test_clone_select_related(self):
        query = Query(Item)
        query.add_select_related(["creator"])
        clone = query.clone()
        clone.add_select_related(["note", "creator__extra"])
        self.assertEqual(query.select_related, {"creator": {}})