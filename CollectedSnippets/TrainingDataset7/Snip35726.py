def test_invalid_view_instance(self):
        class EmptyCBV(View):
            pass

        msg = "view must be a callable, pass EmptyCBV.as_view(), not EmptyCBV()."
        with self.assertRaisesMessage(TypeError, msg):
            path("foo", EmptyCBV())