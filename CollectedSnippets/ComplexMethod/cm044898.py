def test_forge_key_and_config(self):
        forge = get_integration("forge")
        assert forge is not None
        assert forge.key == "forge"
        assert forge.config["folder"] == ".forge/"
        assert forge.config["commands_subdir"] == "commands"
        assert forge.config["requires_cli"] is True
        assert forge.registrar_config["args"] == "{{parameters}}"
        assert forge.registrar_config["extension"] == ".md"
        assert forge.context_file == "AGENTS.md"