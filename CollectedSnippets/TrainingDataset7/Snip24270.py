def test_bbcontains(self):
        # OK City is contained w/in bounding box of Texas.
        okcity = City.objects.get(name="Oklahoma City")
        qs = Country.objects.filter(mpoly__bbcontains=okcity.point)
        self.assertEqual(1, len(qs))
        self.assertEqual("Texas", qs[0].name)