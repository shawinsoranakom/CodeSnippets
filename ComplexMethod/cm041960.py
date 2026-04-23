def add_event(self, created, expiration, s, p, o, content, keywords, poignancy, embedding_pair, filling):
        """
        调用add方法，初始化event
        """
        memory_count = len(self.storage) + 1
        type_count = len(self.event_list) + 1
        memory_type = "event"
        memory_id = f"node_{str(memory_count)}"
        depth = 0

        if "(" in content:
            content = " ".join(content.split()[:3]) + " " + content.split("(")[-1][:-1]

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
            if kw in self.event_keywords:
                self.event_keywords[kw][0:0] = [memory_node]
            else:
                self.event_keywords[kw] = [memory_node]

        self.add(memory_node)

        if f"{p} {o}" != "is idle":
            for kw in keywords:
                if kw in self.kw_strength_event:
                    self.kw_strength_event[kw] += 1
                else:
                    self.kw_strength_event[kw] = 1

        self.embeddings[embedding_pair[0]] = embedding_pair[1]
        return memory_node