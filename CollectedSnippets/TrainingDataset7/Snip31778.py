def test_custom_field_serialization(self):
        """Custom fields serialize and deserialize intact"""
        team_str = "Spartak Moskva"
        player = Player()
        player.name = "Soslan Djanaev"
        player.rank = 1
        player.team = Team(team_str)
        player.save()
        serial_str = serializers.serialize(self.serializer_name, Player.objects.all())
        team = self._get_field_values(serial_str, "team")
        self.assertTrue(team)
        self.assertEqual(team[0], team_str)

        deserial_objs = list(serializers.deserialize(self.serializer_name, serial_str))
        self.assertEqual(
            deserial_objs[0].object.team.to_string(), player.team.to_string()
        )