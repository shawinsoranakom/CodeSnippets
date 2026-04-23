def _items(self):
        if self.i18n:
            # Create (item, lang_code) tuples for all items and languages.
            # This is necessary to paginate with all languages already
            # considered.
            items = [
                (item, lang_code)
                for item in self.items()
                for lang_code in self.get_languages_for_item(item)
            ]
            return items
        return self.items()