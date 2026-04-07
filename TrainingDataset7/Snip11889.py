def get_path_from_parent(self, parent):
        """
        Return a list of PathInfos containing the path from the parent
        model to the current model, or an empty list if parent is not a
        parent of the current model.
        """
        if self.model is parent:
            return []
        model = self.concrete_model
        # Get a reversed base chain including both the current and parent
        # models.
        chain = model._meta.get_base_chain(parent)
        chain.reverse()
        chain.append(model)
        # Construct a list of the PathInfos between models in chain.
        path = []
        for i, ancestor in enumerate(chain[:-1]):
            child = chain[i + 1]
            link = child._meta.get_ancestor_link(ancestor)
            path.extend(link.reverse_path_infos)
        return path