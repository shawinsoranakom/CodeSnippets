def serialize_discovery(self) -> dict[str, Any]:
        """Serialize according to the Discovery API."""
        result: dict[str, Any] = {
            "type": "AlexaInterface",
            "interface": self.name(),
            "version": "3",
        }

        if (instance := self.instance) is not None:
            result["instance"] = instance

        if properties_supported := self.properties_supported():
            result["properties"] = {
                "supported": properties_supported,
                "proactivelyReported": self.properties_proactively_reported(),
                "retrievable": self.properties_retrievable(),
            }

        if (proactively_reported := self.capability_proactively_reported()) is not None:
            result["proactivelyReported"] = proactively_reported

        if (non_controllable := self.properties_non_controllable()) is not None:
            result["properties"]["nonControllable"] = non_controllable

        if (supports_deactivation := self.supports_deactivation()) is not None:
            result["supportsDeactivation"] = supports_deactivation

        if capability_resources := self.capability_resources():
            result["capabilityResources"] = capability_resources

        if configuration := self.configuration():
            result["configuration"] = configuration

        # The plural configurations object is different than the singular
        # configuration object above.
        if configurations := self.configurations():
            result["configurations"] = configurations

        if semantics := self.semantics():
            result["semantics"] = semantics

        if supported_operations := self.supported_operations():
            result["supportedOperations"] = supported_operations

        if inputs := self.inputs():
            result["inputs"] = inputs

        if camera_stream_configurations := self.camera_stream_configurations():
            result["cameraStreamConfigurations"] = camera_stream_configurations

        return result