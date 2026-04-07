def test_rhs_pk(self):
        msg = "CompositePrimaryKey cannot be used as a lookup value."
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(text__gt=F("pk")).count()