def test_cannot_cast_pk(self):
        msg = "Cast expression does not support composite primary keys."
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(text__gt=Cast(F("pk"), TextField())).count()