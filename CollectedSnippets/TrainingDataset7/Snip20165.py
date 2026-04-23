def test_call_order(self):
        with register_lookup(models.DateField, TrackCallsYearTransform):
            # junk lookup - tries lookup, then transform, then fails
            msg = (
                "Unsupported lookup 'junk' for IntegerField or join on the field not "
                "permitted."
            )
            with self.assertRaisesMessage(FieldError, msg):
                Author.objects.filter(birthdate__testyear__junk=2012)
            self.assertEqual(
                TrackCallsYearTransform.call_order, ["lookup", "transform"]
            )
            TrackCallsYearTransform.call_order = []
            # junk transform - tries transform only, then fails
            msg = (
                "Unsupported lookup 'junk__more_junk' for IntegerField or join"
                " on the field not permitted."
            )
            with self.assertRaisesMessage(FieldError, msg):
                Author.objects.filter(birthdate__testyear__junk__more_junk=2012)
            self.assertEqual(TrackCallsYearTransform.call_order, ["transform"])
            TrackCallsYearTransform.call_order = []
            # Just getting the year (implied __exact) - lookup only
            Author.objects.filter(birthdate__testyear=2012)
            self.assertEqual(TrackCallsYearTransform.call_order, ["lookup"])
            TrackCallsYearTransform.call_order = []
            # Just getting the year (explicit __exact) - lookup only
            Author.objects.filter(birthdate__testyear__exact=2012)
            self.assertEqual(TrackCallsYearTransform.call_order, ["lookup"])