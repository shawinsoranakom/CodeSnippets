def test_slow_add_ignore_conflicts(self):
        manager_cls = self.a1.publications.__class__
        # Simulate a race condition between the missing ids retrieval and
        # the bulk insertion attempt.
        missing_target_ids = {self.p1.id}
        # Disable fast-add to test the case where the slow add path is taken.
        add_plan = (True, False, False)
        with mock.patch.object(
            manager_cls, "_get_missing_target_ids", return_value=missing_target_ids
        ) as mocked:
            with mock.patch.object(manager_cls, "_get_add_plan", return_value=add_plan):
                self.a1.publications.add(self.p1)
        mocked.assert_called_once()