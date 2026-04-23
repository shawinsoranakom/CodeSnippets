def test_custom_lookup_with_pk_shortcut(self):
        self.assertEqual(CharPK._meta.pk.name, "char_pk")  # Not equal to 'pk'.
        m = admin.ModelAdmin(CustomIdUser, custom_site)

        abc = CharPK.objects.create(char_pk="abc")
        abcd = CharPK.objects.create(char_pk="abcd")
        m = admin.ModelAdmin(CharPK, custom_site)
        m.search_fields = ["pk__exact"]

        request = self.factory.get("/", data={SEARCH_VAR: "abc"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [abc])

        request = self.factory.get("/", data={SEARCH_VAR: "abcd"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [abcd])