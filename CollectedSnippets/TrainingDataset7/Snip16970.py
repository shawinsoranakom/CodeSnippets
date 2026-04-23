def test_nonaggregate_aggregation_throws(self):
        with self.assertRaisesMessage(TypeError, "fail is not an aggregate expression"):
            Book.objects.aggregate(fail=F("price"))