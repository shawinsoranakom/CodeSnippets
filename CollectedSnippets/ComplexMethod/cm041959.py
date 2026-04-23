def add_thought(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化thought
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.thought_list) + 1
        memory_type = "thought"
        memory_id = f"node_{str(memory_count)}"
        depth = 1

        try:
            if filling:
                depth_list = [memory_node.depth for memory_node in self.storage if memory_node.memory_id in filling]
                depth += max(depth_list)
        except Exception as exp:
            logger.warning(f"filling init occur {exp}")
            pass

        memory_node = BasicMemory(
            memory_id=memory_id,
            memory_count=memory_count,
            type_count=type_count,
            memory_type=memory_type,
            depth=depth,
            created=created,
            expiration=expiration,
            subject=s,
            predicate=p,
            object=o,
            description=content,
            embedding_key=embedding_pair[0],
            poignancy=poignancy,
            keywords=keywords,
            filling=filling,
        )

        keywords = [i.lower() for i in keywords]
        for kw in keywords:
            if kw in self.thought_keywords:
                self.thought_keywords[kw][0:0] = [memory_node]
            else:
                self.thought_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_thought:
                    self.kw_strength_thought[kw] += 1
                else:
                    self.kw_strength_thought[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node