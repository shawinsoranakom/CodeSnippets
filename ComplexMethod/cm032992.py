def _get_updated_content(
        self, courses, start: float, end: float
    ) -> Generator[Document, None, None]:
        for course in courses:
            try:
                contents = self._get_course_contents(course.id)
                for section in contents:
                    for module in section.modules:
                        times = [
                            getattr(module, "timecreated", 0),
                            getattr(module, "timemodified", 0),
                        ]
                        if hasattr(module, "contents"):
                            times.extend(
                                getattr(c, "timemodified", 0)
                                for c in module.contents
                                if c and getattr(c, "timemodified", 0)
                            )
                        last_mod = self._get_latest_timestamp(*times)
                        if start < last_mod <= end:
                            doc = self._process_module(course, section, module)
                            if doc:
                                yield doc
            except Exception as e:
                self._log_error(f"polling course {course.fullname}", e)