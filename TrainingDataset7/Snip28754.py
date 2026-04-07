def test_ptr_accessor_assigns_state(self):
        r = Restaurant.objects.create()
        self.assertIs(r.place_ptr._state.adding, False)
        self.assertEqual(r.place_ptr._state.db, "default")