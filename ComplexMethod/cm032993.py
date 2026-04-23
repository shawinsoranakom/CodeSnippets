def _process_module(self, course, section, module) -> Optional[Document]:
        try:
            mtype = module.modname
            if mtype in ["label", "url"]:
                return None
            if mtype == "resource":
                return self._process_resource(course, section, module)
            if mtype == "forum":
                return self._process_forum(course, section, module)
            if mtype == "page":
                return self._process_page(course, section, module)
            if mtype in ["assign", "quiz"]:
                return self._process_activity(course, section, module)
            if mtype == "book":
                return self._process_book(course, section, module)
        except Exception as e:
            self._log_error(f"processing module {getattr(module, 'name', '?')}", e)
        return None