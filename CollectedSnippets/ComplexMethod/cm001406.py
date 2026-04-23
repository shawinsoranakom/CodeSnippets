def test_get_commands(self):
        """Test that get_commands returns appropriate commands."""
        with TemporaryDirectory() as tmp_dir:
            skill_dir = Path(tmp_dir) / "cmd-test"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """---
name: cmd-test
description: Test
---
Content"""
            )

            config = SkillConfiguration(skill_directories=[Path(tmp_dir)])
            component = SkillComponent(config)

            commands = list(component.get_commands())
            cmd_names = [c.names[0] for c in commands]

            assert "list_skills" in cmd_names
            assert "load_skill" in cmd_names
            # unload_skill and read_skill_file only when skills are loaded
            assert "unload_skill" not in cmd_names

            component.load_skill("cmd-test")
            commands = list(component.get_commands())
            cmd_names = [c.names[0] for c in commands]
            assert "unload_skill" in cmd_names
            assert "read_skill_file" in cmd_names