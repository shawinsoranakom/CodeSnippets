def test_equality(self):
        """
        The path_infos and reverse_path_infos attributes are equivalent to
        calling the get_<method>() with no arguments.
        """
        foreign_object = Membership._meta.get_field("person")
        self.assertEqual(
            foreign_object.path_infos,
            foreign_object.get_path_info(),
        )
        self.assertEqual(
            foreign_object.reverse_path_infos,
            foreign_object.get_reverse_path_info(),
        )