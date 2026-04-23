def combine_with(self, other: "JsonProfile") -> "JsonProfile":
        """
        Combine this profile with another profile by merging their trace events.
        Returns a new JsonProfile object with combined data.
        """
        # Create a new combined data structure
        combined_data = {
            "traceEvents": self.data["traceEvents"] + other.data["traceEvents"],
            "deviceProperties": self.data.get("deviceProperties", []),
        }

        # Merge device properties, avoiding duplicates
        other_device_props = other.data.get("deviceProperties", [])
        existing_device_ids = OrderedSet(
            [dev["id"] for dev in combined_data["deviceProperties"]]
        )

        for device_prop in other_device_props:
            if device_prop["id"] not in existing_device_ids:
                combined_data["deviceProperties"].append(device_prop)

        # Copy any other top-level properties from the first profile
        for key, value in self.data.items():
            if key not in combined_data:
                combined_data[key] = value

        import os

        # Create a temporary file to write the combined data
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            json.dump(combined_data, tmp_file)
            tmp_path = tmp_file.name

        try:
            # Create new JsonProfile from the combined data
            combined_profile = JsonProfile(
                tmp_path,
                benchmark_name=f"{self.benchmark_name or 'Profile1'}_+_{other.benchmark_name or 'Profile2'}",
                dtype=self.dtype or other.dtype,
            )
            return combined_profile
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)