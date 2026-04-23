def get_messages(self) -> Iterator[ChatMessage]:
        # Always provide skill catalog if skills are available
        if self._available_skills:
            catalog_lines = ["## Available Skills"]
            for name, skill in self._available_skills.items():
                loaded_marker = " [LOADED]" if name in self._loaded_skills else ""
                catalog_lines.append(
                    f"- **{name}**{loaded_marker}: {skill.metadata.description}"
                )
            yield ChatMessage.user("\n".join(catalog_lines))

        # Provide loaded skill content
        for name, skill in self._loaded_skills.items():
            if skill.load_level >= SkillLoadLevel.FULL_CONTENT and skill.content:
                skill_content = [f"## Skill: {name}"]
                skill_content.append("")
                skill_content.append(skill.content)

                # Show available additional files
                additional_files = skill.list_additional_files()
                if additional_files:
                    skill_content.append("")
                    skill_content.append("### Additional Files Available")
                    for f in additional_files:
                        loaded = " [loaded]" if f in skill.additional_files else ""
                        skill_content.append(f"- `{f}`{loaded}")

                yield ChatMessage.user("\n".join(skill_content))