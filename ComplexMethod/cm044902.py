def test_valid_descriptor(self, tmp_path):
        p = self._write(tmp_path, VALID_DESCRIPTOR)
        desc = IntegrationDescriptor(p)
        assert desc.id == "my-agent"
        assert desc.name == "My Agent"
        assert desc.version == "1.0.0"
        assert desc.description == "Integration for My Agent"
        assert desc.requires_speckit_version == ">=0.6.0"
        assert len(desc.commands) == 1
        assert desc.scripts == []