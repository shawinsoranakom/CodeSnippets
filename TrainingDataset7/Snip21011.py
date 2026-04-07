def test_only_none_raises_error(self):
        msg = "Cannot pass None as an argument to only()."
        with self.assertRaisesMessage(TypeError, msg):
            Primary.objects.only(None)