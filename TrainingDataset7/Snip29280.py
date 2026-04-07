def test_create_reverse_o2o_error(self):
        msg = "The following fields do not exist in this model: restaurant"
        with self.assertRaisesMessage(ValueError, msg):
            Place.objects.create(restaurant=self.r1)