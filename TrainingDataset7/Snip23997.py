def test03c_layer_references(self):
        """
        Ensure OGR objects keep references to the objects they belong to.
        """
        source = ds_list[0]

        # See ticket #9448.
        def get_layer():
            # This DataSource object is not accessible outside this
            # scope. However, a reference should still be kept alive
            # on the `Layer` returned.
            ds = DataSource(source.ds)
            return ds[0]

        # Making sure we can call OGR routines on the Layer returned.
        lyr = get_layer()
        self.assertEqual(source.nfeat, len(lyr))
        self.assertEqual(source.gtype, lyr.geom_type.num)

        # Same issue for Feature/Field objects, see #18640
        self.assertEqual(str(lyr[0]["str"]), "1")