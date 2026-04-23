def _apply_forge_transformations(self, content: str, template_name: str) -> str:
        """Apply Forge-specific transformations to processed content.

        1. Strip 'handoffs' frontmatter key (from Claude Code templates; incompatible with Forge)
        2. Inject 'name' field if missing (using hyphenated format)
        """
        # Parse frontmatter
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return content

        # Find end of frontmatter
        frontmatter_end = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return content

        frontmatter_lines = lines[1:frontmatter_end]
        body_lines = lines[frontmatter_end + 1:]

        # 1. Strip 'handoffs' key
        filtered_frontmatter = []
        skip_until_outdent = False
        for line in frontmatter_lines:
            if skip_until_outdent:
                # Skip indented lines under handoffs:
                if line and (line[0] == ' ' or line[0] == '\t'):
                    continue
                else:
                    skip_until_outdent = False

            if line.strip().startswith('handoffs:'):
                skip_until_outdent = True
                continue

            filtered_frontmatter.append(line)

        # 2. Inject 'name' field if missing (using centralized formatter)
        has_name = any(line.strip().startswith('name:') for line in filtered_frontmatter)
        if not has_name:
            # Use centralized formatter to ensure consistent hyphenated format
            cmd_name = format_forge_command_name(template_name)
            filtered_frontmatter.insert(0, f'name: {cmd_name}')

        # Reconstruct content
        result = ['---'] + filtered_frontmatter + ['---'] + body_lines
        return '\n'.join(result)