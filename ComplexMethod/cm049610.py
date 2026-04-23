def _search_find_fuzzy_term(self, search_details, search, limit=1000, word_list=None):
        """
        Returns the "closest" match of the search parameter within available words.

        :param search_details: obtained from `_search_get_details()`
        :param search: search term to which words must be matched against
        :param limit: maximum number of records fetched per model to build the word list
        :param word_list: if specified, this list of words is used as possible targets instead of
            the words contained in the match fields of each involved model

        :return: term on which a search can be performed instead of the initial search
        """
        # No fuzzy search for less that 4 characters, multi-words nor 80%+ numbers.
        if len(search) < 4 or ' ' in search or len(re.findall(r'\d', search)) / len(search) >= 0.8:
            return search
        search = search.lower()
        words = set()
        best_score = 0
        best_word = None
        enumerate_words = self._trigram_enumerate_words if self.env.registry.has_trigram else self._basic_enumerate_words
        for word in word_list or enumerate_words(search_details, search, limit):
            if search in word:
                return search
            if word[0] == search[0] and word not in words:
                similarity = similarity_score(search, word)
                if similarity > best_score:
                    best_score = similarity
                    best_word = word
                words.add(word)
        return best_word