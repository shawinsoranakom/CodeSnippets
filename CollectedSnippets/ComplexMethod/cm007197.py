def _update_built_object_and_artifacts(self, result) -> None:
        """Updates the built object and its artifacts."""
        if isinstance(result, tuple):
            if len(result) == 2:  # noqa: PLR2004
                self.built_object, self.artifacts = result
            elif len(result) == 3:  # noqa: PLR2004
                self.custom_component, self.built_object, self.artifacts = result
                self.logs = self.custom_component.get_output_logs()
                for key in self.artifacts:
                    if self.artifacts_raw is None:
                        self.artifacts_raw = {}
                    self.artifacts_raw[key] = self.artifacts[key].get("raw", None)
                    self.artifacts_type[key] = self.artifacts[key].get("type", None) or ArtifactType.UNKNOWN.value
        else:
            self.built_object = result

        for key, value in self.built_object.items():
            self.add_result(key, value)