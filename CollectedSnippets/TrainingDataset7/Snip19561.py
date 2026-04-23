def test_max_pk(self):
        msg = "Max expression does not support composite primary keys."
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.aggregate(Max("pk"))