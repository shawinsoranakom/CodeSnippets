def setUpClass(cls):
        # Avoid referencing __file__ at module level.
        cls.enterClassContext(override_settings(GEOIP_PATH=build_geoip_path()))
        # Always mock host lookup to avoid test breakage if DNS changes.
        cls.enterClassContext(
            mock.patch("socket.gethostbyname", return_value=cls.ipv4_str)
        )

        super().setUpClass()