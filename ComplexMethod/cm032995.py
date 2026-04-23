def _process_book(self, course, section, module) -> Optional[Document]:
        if not getattr(module, "contents", None):
            return None

        contents = module.contents
        chapters = [
            c
            for c in contents
            if getattr(c, "fileurl", None)
            and os.path.basename(c.filename) == "index.html"
        ]
        if not chapters:
            return None

        latest_ts = self._get_latest_timestamp(
            getattr(module, "timecreated", 0),
            getattr(module, "timemodified", 0),
            *[getattr(c, "timecreated", 0) for c in contents],
            *[getattr(c, "timemodified", 0) for c in contents],
        )

        markdown_parts = [f"# {module.name}\n"]
        chapter_info = []

        for ch in chapters:
            try:
                resp = rl_requests.get(self._add_token_to_url(ch.fileurl), timeout=60)
                resp.raise_for_status()
                html = resp.content.decode("utf-8", errors="ignore")
                markdown_parts.append(md(html) + "\n\n---\n")

                # Collect chapter information for metadata
                chapter_info.append(
                    {
                        "chapter_id": getattr(ch, "chapterid", None),
                        "title": getattr(ch, "title", None),
                        "filename": getattr(ch, "filename", None),
                        "fileurl": getattr(ch, "fileurl", None),
                        "time_created": getattr(ch, "timecreated", None),
                        "time_modified": getattr(ch, "timemodified", None),
                        "size": getattr(ch, "filesize", None),
                    }
                )
            except Exception as e:
                self._log_error(f"processing book chapter {ch.filename}", e)

        blob = "\n".join(markdown_parts).encode("utf-8")
        semantic_id = f"{course.fullname} / {section.name} / {module.name}"

        # Create metadata dictionary with relevant information
        metadata = {
            "moodle_url": self.moodle_url,
            "course_id": getattr(course, "id", None),
            "course_name": getattr(course, "fullname", None),
            "course_shortname": getattr(course, "shortname", None),
            "section_id": getattr(section, "id", None),
            "section_name": getattr(section, "name", None),
            "section_number": getattr(section, "section", None),
            "module_id": getattr(module, "id", None),
            "module_name": getattr(module, "name", None),
            "module_type": getattr(module, "modname", None),
            "book_id": getattr(module, "instance", None),
            "chapter_count": len(chapters),
            "chapters": chapter_info,
            "time_created": getattr(module, "timecreated", None),
            "time_modified": getattr(module, "timemodified", None),
            "visible": getattr(module, "visible", None),
            "groupmode": getattr(module, "groupmode", None),
        }

        return Document(
            id=f"moodle_book_{module.id}",
            source="moodle",
            semantic_identifier=semantic_id,
            extension=".md",
            blob=blob,
            doc_updated_at=datetime.fromtimestamp(latest_ts or 0, tz=timezone.utc),
            size_bytes=len(blob),
            metadata=metadata,
        )