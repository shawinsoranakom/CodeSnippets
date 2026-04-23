def geometries(self):
        # Load up the test geometry data from fixture into global.
        with open(os.path.join(TEST_DATA, "geometries.json")) as f:
            geometries = json.load(f)
        return TestGeomSet(**strconvert(geometries))