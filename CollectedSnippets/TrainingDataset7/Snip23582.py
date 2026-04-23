def test_coerce_object_id_remote_field_cache_persistence(self):
        restaurant = Restaurant.objects.create()
        CharLink.objects.create(content_object=restaurant)
        charlink = CharLink.objects.latest("pk")
        self.assertIs(charlink.content_object, charlink.content_object)
        # If the model (Cafe) uses more than one level of multi-table
        # inheritance.
        cafe = Cafe.objects.create()
        CharLink.objects.create(content_object=cafe)
        charlink = CharLink.objects.latest("pk")
        self.assertIs(charlink.content_object, charlink.content_object)