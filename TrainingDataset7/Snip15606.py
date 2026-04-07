def check_ordering_of_field_choices(self, correct_ordering):
        fk_field = site.get_model_admin(Song).formfield_for_foreignkey(
            Song.band.field, request=None
        )
        m2m_field = site.get_model_admin(Song).formfield_for_manytomany(
            Song.other_interpreters.field, request=None
        )
        self.assertEqual(list(fk_field.queryset), correct_ordering)
        self.assertEqual(list(m2m_field.queryset), correct_ordering)