def _chunk_markdown_by_headings(
        self, file_path: Path, min_heading_level: int = 2
    ) -> list[MarkdownSection]:
        """
        Split a markdown file into sections based on headings.

        Args:
            file_path: Path to the markdown file
            min_heading_level: Minimum heading level to split on (default: 2 for ##)

        Returns:
            List of MarkdownSection objects, one per section.
            If no headings found, returns a single section with all content.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []

        lines = content.split("\n")
        sections: list[MarkdownSection] = []
        current_section_lines: list[str] = []
        current_title = ""
        current_level = 0
        section_index = 0
        doc_title = ""

        for line in lines:
            # Check if line is a heading
            if line.startswith("#"):
                # Count heading level
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                heading_text = line[level:].strip()

                # Track document title (level 1 heading)
                if level == 1 and not doc_title:
                    doc_title = heading_text
                    # Don't create a section for just the title - add it to first section
                    current_section_lines.append(line)
                    continue

                # Check if this heading should start a new section
                if level >= min_heading_level:
                    # Save previous section if it has content
                    if current_section_lines:
                        section_content = "\n".join(current_section_lines).strip()
                        if section_content:
                            # Use doc title for first section if no specific title
                            title = current_title if current_title else doc_title
                            if not title:
                                title = file_path.stem.replace("-", " ").replace(
                                    "_", " "
                                )
                            sections.append(
                                MarkdownSection(
                                    title=title,
                                    content=section_content,
                                    level=current_level if current_level else 1,
                                    index=section_index,
                                )
                            )
                            section_index += 1

                    # Start new section
                    current_section_lines = [line]
                    current_title = heading_text
                    current_level = level
                else:
                    # Lower level heading (e.g., # when splitting on ##)
                    current_section_lines.append(line)
            else:
                current_section_lines.append(line)

        # Don't forget the last section
        if current_section_lines:
            section_content = "\n".join(current_section_lines).strip()
            if section_content:
                title = current_title if current_title else doc_title
                if not title:
                    title = file_path.stem.replace("-", " ").replace("_", " ")
                sections.append(
                    MarkdownSection(
                        title=title,
                        content=section_content,
                        level=current_level if current_level else 1,
                        index=section_index,
                    )
                )

        # If no sections were created (no headings found), create one section with all content
        if not sections and content.strip():
            title = (
                doc_title
                if doc_title
                else file_path.stem.replace("-", " ").replace("_", " ")
            )
            sections.append(
                MarkdownSection(
                    title=title,
                    content=content.strip(),
                    level=1,
                    index=0,
                )
            )

        return sections