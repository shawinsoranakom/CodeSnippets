def test_core(self):
        # lt + different version strings
        require_version_core("numpy<1000.4.5")
        require_version_core("numpy<1000.4")
        require_version_core("numpy<1000")

        # le
        require_version_core("numpy<=1000.4.5")
        require_version_core(f"numpy<={numpy_ver}")

        # eq
        require_version_core(f"numpy=={numpy_ver}")

        # ne
        require_version_core("numpy!=1000.4.5")

        # ge
        require_version_core("numpy>=1.0")
        require_version_core("numpy>=1.0.0")
        require_version_core(f"numpy>={numpy_ver}")

        # gt
        require_version_core("numpy>1.0.0")

        # mix
        require_version_core("numpy>1.0.0,<1000")

        # requirement w/o version
        require_version_core("numpy")

        # unmet requirements due to version conflict
        for req in ["numpy==1.0.0", "numpy>=1000.0.0", f"numpy<{numpy_ver}"]:
            try:
                require_version_core(req)
            except ImportError as e:
                self.assertIn(f"{req} is required", str(e))
                self.assertIn("but found", str(e))

        # unmet requirements due to missing module
        for req in ["numpipypie>1", "numpipypie2"]:
            try:
                require_version_core(req)
            except importlib.metadata.PackageNotFoundError as e:
                self.assertIn(f"The '{req}' distribution was not found and is required by this application", str(e))
                self.assertIn("Try: `pip install transformers -U`", str(e))

        # bogus requirements formats:
        # 1. whole thing
        for req in ["numpy??1.0.0", "numpy1.0.0"]:
            try:
                require_version_core(req)
            except ValueError as e:
                self.assertIn("requirement needs to be in the pip package format", str(e))
        # 2. only operators
        for req in ["numpy=1.0.0", "numpy == 1.00", "numpy<>1.0.0", "numpy><1.00", "numpy>>1.0.0"]:
            try:
                require_version_core(req)
            except ValueError as e:
                self.assertIn("need one of ", str(e))