def load(self, memory_saved: Path):
        """
        将GA的JSON解析，填充到AgentMemory类之中
        """
        self.embeddings = read_json_file(memory_saved.joinpath("embeddings.json"))
        memory_load = read_json_file(memory_saved.joinpath("nodes.json"))
        for count in range(len(memory_load.keys())):
            node_id = f"node_{str(count + 1)}"
            node_details = memory_load[node_id]
            node_type = node_details["type"]
            created = datetime.strptime(node_details["created"], "%Y-%m-%d %H:%M:%S")
            expiration = None
            if node_details["expiration"]:
                expiration = datetime.strptime(node_details["expiration"], "%Y-%m-%d %H:%M:%S")

            s = node_details["subject"]
            p = node_details["predicate"]
            o = node_details["object"]

            description = node_details["description"]
            embedding_pair = (node_details["embedding_key"], self.embeddings[node_details["embedding_key"]])
            poignancy = node_details["poignancy"]
            keywords = set(node_details["keywords"])
            filling = node_details["filling"]
            if node_type == "thought":
                self.add_thought(
                    created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling
                )
            if node_type == "event":
                self.add_event(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)
            if node_type == "chat":
                self.add_chat(created, expiration, s, p, o, description, keywords, poignancy, embedding_pair, filling)

        strength_keywords_load = read_json_file(memory_saved.joinpath("kw_strength.json"))
        if strength_keywords_load["kw_strength_event"]:
            self.kw_strength_event = strength_keywords_load["kw_strength_event"]
        if strength_keywords_load["kw_strength_thought"]:
            self.kw_strength_thought = strength_keywords_load["kw_strength_thought"]