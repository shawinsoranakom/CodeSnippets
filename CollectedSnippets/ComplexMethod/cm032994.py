def _process_forum(self, course, section, module) -> Optional[Document]:
        if not self.moodle_client or not getattr(module, "instance", None):
            return None

        try:
            result = self.moodle_client.mod.forum.get_forum_discussions(
                forumid=module.instance
            )
            disc_list = getattr(result, "discussions", [])
            if not disc_list:
                return None

            markdown = [f"# {module.name}\n"]
            latest_ts = self._get_latest_timestamp(
                getattr(module, "timecreated", 0),
                getattr(module, "timemodified", 0),
            )

            for d in disc_list:
                markdown.append(f"## {d.name}\n\n{md(d.message or '')}\n\n---\n")
                latest_ts = max(latest_ts, getattr(d, "timemodified", 0))

            blob = "\n".join(markdown).encode("utf-8")
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
                "forum_id": getattr(module, "instance", None),
                "discussion_count": len(disc_list),
                "time_created": getattr(module, "timecreated", None),
                "time_modified": getattr(module, "timemodified", None),
                "visible": getattr(module, "visible", None),
                "groupmode": getattr(module, "groupmode", None),
                "discussions": [
                    {
                        "id": getattr(d, "id", None),
                        "name": getattr(d, "name", None),
                        "user_id": getattr(d, "userid", None),
                        "user_fullname": getattr(d, "userfullname", None),
                        "time_created": getattr(d, "timecreated", None),
                        "time_modified": getattr(d, "timemodified", None),
                    }
                    for d in disc_list
                ],
            }

            return Document(
                id=f"moodle_forum_{module.id}",
                source="moodle",
                semantic_identifier=semantic_id,
                extension=".md",
                blob=blob,
                doc_updated_at=datetime.fromtimestamp(latest_ts or 0, tz=timezone.utc),
                size_bytes=len(blob),
                metadata=metadata,
            )
        except Exception as e:
            self._log_error(f"processing forum {module.name}", e)
            return None