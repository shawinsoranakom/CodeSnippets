def test_skill_description_from_first_heading(self):
        """Verify that each SKILL.md has the expected markdown heading (after YAML frontmatter)."""
        for skill_name, expected_heading in self.EXPECTED_SKILLS.items():
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            content = skill_file.read_text(encoding="utf-8")
            # Skip YAML frontmatter block (--- ... ---)
            lines = content.splitlines()
            in_frontmatter = lines[0].strip() == "---" if lines else False
            heading = ""
            for i, line in enumerate(lines):
                if i == 0 and in_frontmatter:
                    continue
                if in_frontmatter and line.strip() == "---":
                    in_frontmatter = False
                    continue
                if not in_frontmatter and line.startswith("#"):
                    heading = line.lstrip("# ").strip()
                    break
            assert (
                heading == expected_heading
            ), f"Skill '{skill_name}' heading mismatch: got '{heading}', expected '{expected_heading}'"