def test_unknown_kwarg(self):
        s = SelfRef.objects.create()
        msg = "refresh_from_db() got an unexpected keyword argument 'unknown_kwarg'"
        with self.assertRaisesMessage(TypeError, msg):
            s.refresh_from_db(unknown_kwarg=10)