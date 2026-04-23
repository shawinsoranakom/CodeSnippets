def filter_content(self, html: str, min_word_threshold: int = None) -> List[str]:
        """
        Implements content filtering using BM25 algorithm with priority tag handling.

            Note:
        This method implements the filtering logic for the BM25ContentFilter class.
        It takes HTML content as input and returns a list of filtered text chunks.

        Args:
            html (str): HTML content to be filtered.
            min_word_threshold (int): Minimum word threshold for filtering (optional).

        Returns:
            List[str]: List of filtered text chunks.
        """
        if not html or not isinstance(html, str):
            return []

        soup = BeautifulSoup(html, "lxml")

        # Check if body is present
        if not soup.body:
            # Wrap in body tag if missing
            soup = BeautifulSoup(f"<body>{html}</body>", "lxml")
        body = soup.find("body")

        query = self.extract_page_query(soup, body)

        if not query:
            return []
            # return [self.clean_element(soup)]

        candidates = self.extract_text_chunks(body, min_word_threshold)

        if not candidates:
            return []

        # Tokenize corpus
        # tokenized_corpus = [chunk.lower().split() for _, chunk, _, _ in candidates]
        # tokenized_query = query.lower().split()

        # tokenized_corpus = [[ps.stem(word) for word in chunk.lower().split()]
        #                 for _, chunk, _, _ in candidates]
        # tokenized_query = [ps.stem(word) for word in query.lower().split()]

        if self.use_stemming:
            tokenized_corpus = [
                [self.stemmer.stemWord(word) for word in chunk.lower().split()]
                for _, chunk, _, _ in candidates
            ]
            tokenized_query = [
                self.stemmer.stemWord(word) for word in query.lower().split()
            ]
        else:
            tokenized_corpus = [
                chunk.lower().split() for _, chunk, _, _ in candidates
            ]
            tokenized_query = query.lower().split()

        # tokenized_corpus = [[self.stemmer.stemWord(word) for word in tokenize_text(chunk.lower())]
        #            for _, chunk, _, _ in candidates]
        # tokenized_query = [self.stemmer.stemWord(word) for word in tokenize_text(query.lower())]

        # Clean from stop words and noise
        tokenized_corpus = [clean_tokens(tokens) for tokens in tokenized_corpus]
        tokenized_query = clean_tokens(tokenized_query)

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        # Adjust scores with tag weights
        adjusted_candidates = []
        for score, (index, chunk, tag_type, tag) in zip(scores, candidates):
            tag_weight = self.priority_tags.get(tag.name, 1.0)
            adjusted_score = score * tag_weight
            adjusted_candidates.append((adjusted_score, index, chunk, tag))

        # Filter candidates by threshold
        selected_candidates = [
            (index, chunk, tag)
            for adjusted_score, index, chunk, tag in adjusted_candidates
            if adjusted_score >= self.bm25_threshold
        ]

        if not selected_candidates:
            return []

        # Sort selected candidates by original document order
        selected_candidates.sort(key=lambda x: x[0])

        # Deduplicate by chunk text, keeping first occurrence (lowest index)
        seen_texts = set()
        unique_candidates = []
        for index, chunk, tag in selected_candidates:
            if chunk not in seen_texts:
                seen_texts.add(chunk)
                unique_candidates.append((index, chunk, tag))

        return [self.clean_element(tag) for _, _, tag in unique_candidates]