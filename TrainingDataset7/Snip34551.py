def inner(self):
            # Set up custom template tag libraries if specified
            libraries = getattr(self, "libraries", {})

            self.engine = Engine(
                libraries=libraries,
                loaders=loaders,
                debug=debug_only,
            )
            func(self)
            if test_once:
                return
            func(self)
            if debug_only:
                return

            self.engine = Engine(
                libraries=libraries,
                loaders=loaders,
                string_if_invalid="INVALID",
            )
            func(self)
            func(self)

            self.engine = Engine(
                debug=True,
                libraries=libraries,
                loaders=loaders,
            )
            func(self)
            func(self)