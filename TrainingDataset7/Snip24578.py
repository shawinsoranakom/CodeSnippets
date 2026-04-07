def test12a_count(self):
        "Testing `Count` aggregate on geo-fields."
        # The City, 'Fort Worth' uses the same location as Dallas.
        dallas = City.objects.get(name="Dallas")

        # Count annotation should be 2 for the Dallas location now.
        loc = Location.objects.annotate(num_cities=Count("city")).get(
            id=dallas.location.id
        )
        self.assertEqual(2, loc.num_cities)