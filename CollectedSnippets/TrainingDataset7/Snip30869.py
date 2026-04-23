def test_ticket_19964(self):
        my1 = MyObject.objects.create(data="foo")
        my1.parent = my1
        my1.save()
        my2 = MyObject.objects.create(data="bar", parent=my1)
        parents = MyObject.objects.filter(parent=F("id"))
        children = MyObject.objects.filter(parent__in=parents).exclude(parent=F("id"))
        self.assertEqual(list(parents), [my1])
        # Evaluating the children query (which has parents as part of it) does
        # not change results for the parents query.
        self.assertEqual(list(children), [my2])
        self.assertEqual(list(parents), [my1])