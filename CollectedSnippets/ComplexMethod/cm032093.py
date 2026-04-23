def _should_extract_element(self, element) -> bool:
        """判断是否应该提取某个元素

        Args:
            element: 文档元素

        Returns:
            bool: 是否应该提取
        """
        if isinstance(element, (Text, NarrativeText)):
            return True

        if isinstance(element, Title) and self.config.extract_titles:
            return True

        if isinstance(element, ListItem) and self.config.extract_lists:
            return True

        if isinstance(element, Table) and self.config.extract_tables:
            return True

        if isinstance(element, (Header, Footer)) and self.config.extract_headers_footers:
            return True

        return False