def register_embedding_by_name(self, embedding, model, name):
        ids = model.cond_stage_model.tokenize([name])[0]
        first_id = ids[0]
        if first_id not in self.ids_lookup:
            self.ids_lookup[first_id] = []
        if name in self.word_embeddings:
            # remove old one from the lookup list
            lookup = [x for x in self.ids_lookup[first_id] if x[1].name!=name]
        else:
            lookup = self.ids_lookup[first_id]
        if embedding is not None:
            lookup += [(ids, embedding)]
        self.ids_lookup[first_id] = sorted(lookup, key=lambda x: len(x[0]), reverse=True)
        if embedding is None:
            # unregister embedding with specified name
            if name in self.word_embeddings:
                del self.word_embeddings[name]
            if len(self.ids_lookup[first_id])==0:
                del self.ids_lookup[first_id]
            return None
        self.word_embeddings[name] = embedding
        return embedding