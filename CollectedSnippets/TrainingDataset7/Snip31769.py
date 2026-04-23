def test_serialize_unicode_roundtrip(self):
        """Unicode makes the roundtrip intact"""
        actor_name = "Za\u017c\u00f3\u0142\u0107"
        movie_title = "G\u0119\u015bl\u0105 ja\u017a\u0144"
        ac = Actor(name=actor_name)
        mv = Movie(title=movie_title, actor=ac)
        ac.save()
        mv.save()

        serial_str = serializers.serialize(self.serializer_name, [mv])
        self.assertEqual(self._get_field_values(serial_str, "title")[0], movie_title)
        self.assertEqual(self._get_field_values(serial_str, "actor")[0], actor_name)

        obj_list = list(serializers.deserialize(self.serializer_name, serial_str))
        mv_obj = obj_list[0].object
        self.assertEqual(mv_obj.title, movie_title)