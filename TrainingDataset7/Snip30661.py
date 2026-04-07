def test_ticket10181(self):
        # Avoid raising an EmptyResultSet if an inner query is probably
        # empty (and hence, not executed).
        self.assertSequenceEqual(
            Tag.objects.filter(id__in=Tag.objects.filter(id__in=[])), []
        )