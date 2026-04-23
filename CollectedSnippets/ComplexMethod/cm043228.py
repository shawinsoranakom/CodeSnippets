def extract(self, url: str, html: str, *q, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract clusters from HTML content using hierarchical clustering.

        Args:
            url (str): The URL of the webpage.
            html (str): The HTML content of the webpage.

        Returns:
            List[Dict[str, Any]]: A list of processed JSON blocks.
        """
        # Assume `html` is a list of text chunks for this strategy
        t = time.time()
        # Split by delimiter; fall back to double-newline splitting for raw text
        text_chunks = html.split(self.DEL)
        if len(text_chunks) == 1:
            text_chunks = [chunk.strip() for chunk in html.split("\n\n") if chunk.strip()]

        # Pre-filter documents using embeddings and semantic_filter
        text_chunks = self.filter_documents_embeddings(
            text_chunks, self.semantic_filter
        )

        if not text_chunks:
            return []

        # Perform clustering
        labels = self.hierarchical_clustering(text_chunks)
        # print(f"[LOG] 🚀 Clustering done in {time.time() - t:.2f} seconds")

        # Organize texts by their cluster labels, retaining order
        t = time.time()
        clusters = {}
        for index, label in enumerate(labels):
            clusters.setdefault(label, []).append(text_chunks[index])

        # Filter clusters by word count
        filtered_clusters = self.filter_clusters_by_word_count(clusters)

        # Convert filtered clusters to a sorted list of dictionaries
        cluster_list = [
            {"index": int(idx), "tags": [], "content": " ".join(filtered_clusters[idx])}
            for idx in sorted(filtered_clusters)
        ]

        if self.verbose:
            print(f"[LOG] 🚀 Assign tags using {self.device}")

        if self.device.type in ["gpu", "cuda", "mps", "cpu"]:
            labels = self.nlp([cluster["content"] for cluster in cluster_list])

            for cluster, label in zip(cluster_list, labels):
                cluster["tags"] = label
        # elif self.device.type == "cpu":
        #     # Process the text with the loaded model
        #     texts = [cluster['content'] for cluster in cluster_list]
        #     # Batch process texts
        #     docs = self.nlp.pipe(texts, disable=["tagger", "parser", "ner", "lemmatizer"])

        #     for doc, cluster in zip(docs, cluster_list):
        #         tok_k = self.top_k
        #         top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
        #         cluster['tags'] = [cat for cat, _ in top_categories]

        # for cluster in  cluster_list:
        #     doc = self.nlp(cluster['content'])
        #     tok_k = self.top_k
        #     top_categories = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)[:tok_k]
        #     cluster['tags'] = [cat for cat, _ in top_categories]

        if self.verbose:
            print(f"[LOG] 🚀 Categorization done in {time.time() - t:.2f} seconds")

        return cluster_list