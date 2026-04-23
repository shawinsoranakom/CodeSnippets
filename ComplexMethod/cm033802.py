def _validate_all_semantic_markup(self, docs, return_docs):
        if not isinstance(docs, dict):
            docs = {}
        if not isinstance(return_docs, dict):
            return_docs = {}

        self._all_options = set()
        self._all_return_values = set()
        self._validate_semantic_markup_collect(self._all_options, 'suboptions', docs.get('options'), [[]])
        self._validate_semantic_markup_collect(self._all_return_values, 'contains', return_docs, [[]])

        for string_keys in ('short_description', 'description', 'notes', 'requirements', 'todo'):
            self._validate_semantic_markup(docs.get(string_keys))

        if is_iterable(docs.get('seealso')):
            for entry in docs.get('seealso'):
                if isinstance(entry, dict):
                    self._validate_semantic_markup(entry.get('description'))

        if isinstance(docs.get('attributes'), dict):
            for entry in docs.get('attributes').values():
                if isinstance(entry, dict):
                    for key in ('description', 'details'):
                        self._validate_semantic_markup(entry.get(key))

        if isinstance(docs.get('deprecated'), dict):
            for key in ('why', 'alternative', 'alternatives'):
                self._validate_semantic_markup(docs.get('deprecated').get(key))

        self._validate_semantic_markup_options(docs.get('options'))
        self._validate_semantic_markup_return_values(return_docs)