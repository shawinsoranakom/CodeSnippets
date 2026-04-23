async def merge(
        self, query: str, indices_list: List[List[Union[NodeWithScore, TextScore]]]
    ) -> List[Union[NodeWithScore, TextScore]]:
        """Merge results from multiple indices based on the query.

        Args:
            query (str): The search query.
            indices_list (List[List[Union[NodeWithScore, TextScore]]]): A list of result lists from different indices.

        Returns:
            List[Union[NodeWithScore, TextScore]]: A list of merged results sorted by similarity.
        """
        flat_nodes = [node for indices in indices_list if indices for node in indices if node]
        if len(flat_nodes) <= self.recall_count:
            return flat_nodes

        if not self.embedding:
            if self.model:
                config.embedding.model = self.model
            factory = RAGEmbeddingFactory(config)
            self.embedding = factory.get_rag_embedding()

        scores = []
        query_embedding = await self.embedding.aget_text_embedding(query)
        for i in flat_nodes:
            try:
                text_embedding = await self.embedding.aget_text_embedding(i.text)
            except Exception as e:  # 超过最大长度
                tenth = int(len(i.text) / 10)  # DEFAULT_MIN_TOKEN_COUNT = 10000
                logger.warning(
                    f"{e}, tenth len={tenth}, pre_part_len={len(i.text[: tenth * 6])}, post_part_len={len(i.text[tenth * 4:])}"
                )
                pre_win_part = await self.embedding.aget_text_embedding(i.text[: tenth * 6])
                post_win_part = await self.embedding.aget_text_embedding(i.text[tenth * 4 :])
                similarity = max(
                    self.embedding.similarity(query_embedding, pre_win_part),
                    self.embedding.similarity(query_embedding, post_win_part),
                )
                scores.append((similarity, i))
                continue
            similarity = self.embedding.similarity(query_embedding, text_embedding)
            scores.append((similarity, i))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [i[1] for i in scores][: self.recall_count]