def test_sliced_queryset(self):
        msg = "Cannot create distinct fields once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Staff.objects.all()[0:5].distinct("name")