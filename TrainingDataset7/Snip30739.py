def test_ticket_19151(self):
        # #19151 -- Calling .values() or .values_list() on an empty QuerySet
        # should return an empty QuerySet and not cause an error.
        q = Author.objects.none()
        self.assertCountEqual(q.values(), [])
        self.assertCountEqual(q.values_list(), [])