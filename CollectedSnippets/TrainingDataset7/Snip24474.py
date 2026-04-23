def tearDown(self):
        # Delete table after testing
        if hasattr(self, "current_state"):
            self.apply_operations(
                "gis", self.current_state, [migrations.DeleteModel("Neighborhood")]
            )
        super().tearDown()