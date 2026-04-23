def test_create_diamond_mti_default_pk(self):
        # 1 INSERT for each base.
        with self.assertNumQueries(4):
            common_child = CommonChild.objects.create()
        # 3 SELECTs for the parents, 1 UPDATE for the child.
        with self.assertNumQueries(4):
            common_child.save()