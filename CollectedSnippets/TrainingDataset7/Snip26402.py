def test_add_remove_set_by_pk_raises(self):
        usa = Country.objects.create(name="United States")
        chicago = City.objects.create(name="Chicago")
        msg = "'City' instance expected, got %r" % chicago.pk
        with self.assertRaisesMessage(TypeError, msg):
            usa.cities.add(chicago.pk)
        with self.assertRaisesMessage(TypeError, msg):
            usa.cities.remove(chicago.pk)
        with self.assertRaisesMessage(TypeError, msg):
            usa.cities.set([chicago.pk])