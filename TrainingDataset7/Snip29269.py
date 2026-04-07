def test_save_nullable_o2o_after_parent(self):
        place = Place(name="Rose tattoo")
        bar = UndergroundBar(place=place)
        place.save()
        bar.save()
        bar.refresh_from_db()
        self.assertEqual(bar.place, place)