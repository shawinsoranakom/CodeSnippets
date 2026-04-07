def test09_pk_relations(self):
        """
        Ensuring correct primary key column is selected across relations. See
        #10757.
        """
        # The expected ID values -- notice the last two location IDs
        # are out of order. Dallas and Houston have location IDs that differ
        # from their PKs -- this is done to ensure that the related location
        # ID column is selected instead of ID column for the city.
        city_ids = (1, 2, 3, 4, 5)
        loc_ids = (1, 2, 3, 5, 4)
        ids_qs = City.objects.order_by("id").values("id", "location__id")
        for val_dict, c_id, l_id in zip(ids_qs, city_ids, loc_ids):
            self.assertEqual(val_dict["id"], c_id)
            self.assertEqual(val_dict["location__id"], l_id)