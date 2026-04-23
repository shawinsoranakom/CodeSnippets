def test_layermap_unique_multigeometry_fk(self):
        """
        The `unique`, and `transform`, geometry collection conversion, and
        ForeignKey mappings.
        """
        # All the following should work.

        # Telling LayerMapping that we want no transformations performed on the
        # data.
        lm = LayerMapping(County, co_shp, co_mapping, transform=False)

        # Specifying the source spatial reference system via the `source_srs`
        # keyword.
        lm = LayerMapping(County, co_shp, co_mapping, source_srs=4269)
        lm = LayerMapping(County, co_shp, co_mapping, source_srs="NAD83")

        # Unique may take tuple or string parameters.
        for arg in ("name", ("name", "mpoly")):
            lm = LayerMapping(County, co_shp, co_mapping, transform=False, unique=arg)

        # Now test for failures

        # Testing invalid params for the `unique` keyword.
        for e, arg in (
            (TypeError, 5.0),
            (ValueError, "foobar"),
            (ValueError, ("name", "mpolygon")),
        ):
            with self.assertRaises(e):
                LayerMapping(County, co_shp, co_mapping, transform=False, unique=arg)

        # No source reference system defined in the shapefile, should raise an
        # error.
        if connection.features.supports_transform:
            with self.assertRaises(LayerMapError):
                LayerMapping(County, co_shp, co_mapping)

        # Passing in invalid ForeignKey mapping parameters -- must be a
        # dictionary mapping for the model the ForeignKey points to.
        bad_fk_map1 = copy(co_mapping)
        bad_fk_map1["state"] = "name"
        bad_fk_map2 = copy(co_mapping)
        bad_fk_map2["state"] = {"nombre": "State"}
        with self.assertRaises(TypeError):
            LayerMapping(County, co_shp, bad_fk_map1, transform=False)
        with self.assertRaises(LayerMapError):
            LayerMapping(County, co_shp, bad_fk_map2, transform=False)

        # There exist no State models for the ForeignKey mapping to work --
        # should raise a MissingForeignKey exception (this error would be
        # ignored if the `strict` keyword is not set).
        lm = LayerMapping(County, co_shp, co_mapping, transform=False, unique="name")
        with self.assertRaises(MissingForeignKey):
            lm.save(silent=True, strict=True)

        # Now creating the state models so the ForeignKey mapping may work.
        State.objects.bulk_create(
            [State(name="Colorado"), State(name="Hawaii"), State(name="Texas")]
        )

        # If a mapping is specified as a collection, all OGR fields that
        # are not collections will be converted into them. For example, a Point
        # column would be converted to MultiPoint. Other things being done
        # w/the keyword args:
        #  `transform=False`: Specifies that no transform is to be done; this
        #    has the effect of ignoring the spatial reference check (because
        #    the county shapefile does not have implicit spatial reference
        #    info).
        #
        #  `unique='name'`: Creates models on the condition that they have
        #    unique county names; geometries from each feature however will be
        #    appended to the geometry collection of the unique model. Thus,
        #    all of the various islands in Honolulu county will be in one
        #    database record with a MULTIPOLYGON type.
        lm = LayerMapping(County, co_shp, co_mapping, transform=False, unique="name")
        lm.save(silent=True, strict=True)

        # A reference that doesn't use the unique keyword; a new database
        # record will created for each polygon.
        lm = LayerMapping(CountyFeat, co_shp, cofeat_mapping, transform=False)
        lm.save(silent=True, strict=True)

        # The county helper is called to ensure integrity of County models.
        self.county_helper()