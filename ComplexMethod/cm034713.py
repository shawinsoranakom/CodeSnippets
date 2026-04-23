def add_source(self, source: Union[Dict[str, str], str]) -> None:
        """Add a source to the list, cleaning the URL if necessary."""
        source = source if isinstance(source, dict) else {"url": source}
        url = source.get("url", source.get("link", None))
        if not url:
            return

        url = re.sub(r"[&?]utm_source=.+", "", url)
        source["url"] = url

        ref_info = self.get_ref_info(source)
        if ref_info:
            existing_source, idx = self.find_by_ref_info(ref_info)
            if existing_source and idx is not None:
                self.list[idx] = source
                return

        existing_source, idx = self.find_by_url(source["url"])
        if existing_source and idx is not None:
            self.list[idx] = source
            return

        self.list.append(source)