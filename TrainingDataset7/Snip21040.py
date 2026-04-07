def test_defer_inheritance_pk_chaining(self):
        """
        When an inherited model is fetched from the DB, its PK is also fetched.
        When getting the PK of the parent model it is useful to use the already
        fetched parent model PK if it happens to be available.
        """
        s1 = Secondary.objects.create(first="x1", second="y1")
        bc = BigChild.objects.create(name="b1", value="foo", related=s1, other="bar")
        bc_deferred = BigChild.objects.only("name").get(pk=bc.pk)
        with self.assertNumQueries(0):
            bc_deferred.id
        self.assertEqual(bc_deferred.pk, bc_deferred.id)