def test_object_update(self):
        # F expressions can be used to update attributes on single objects
        self.gmbh.num_employees = F("num_employees") + 4
        self.gmbh.save()
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(self.gmbh.num_employees, 36)