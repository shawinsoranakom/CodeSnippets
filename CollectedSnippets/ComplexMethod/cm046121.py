def update_markdown_files(md_filepath: Path):
    """Create or update a Markdown file, ensuring frontmatter is present."""
    if md_filepath.exists():
        content = md_filepath.read_text().strip()

        # Replace apostrophes
        content = content.replace("‘", "'").replace("’", "'")

        # Add frontmatter if missing
        if not content.strip().startswith("---\n"):
            header = "---\ncomments: true\ndescription: TODO ADD DESCRIPTION\nkeywords: TODO ADD KEYWORDS\n---\n\n"
            content = header + content

        # Ensure MkDocs admonitions "=== " lines are preceded and followed by empty newlines
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("=== "):
                if i > 0 and new_lines[-1] != "":
                    new_lines.append("")
                new_lines.append(line)
                if i < len(lines) - 1 and lines[i + 1].strip() != "":
                    new_lines.append("")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

        # Add EOF newline if missing
        if not content.endswith("\n"):
            content += "\n"

        # Save page
        md_filepath.write_text(content)
    return