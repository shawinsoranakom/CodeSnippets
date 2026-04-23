def _operator_parent_of_domain(comodel: BaseModel, parent):
    """Return a set of ids or a domain to find all parents of given model"""
    parent_ids: OrderedSet[int]
    if comodel._parent_store and parent == comodel._parent_name:
        try:
            paths = comodel.mapped('parent_path')
        except MissingError:
            paths = comodel.exists().mapped('parent_path')
        parent_ids = OrderedSet(
            int(label)
            for path in paths
            for label in path.split('/')[:-1]
        )
    else:
        # recursively retrieve all parent nodes with sudo() to avoid
        # access rights errors; the filtering of forbidden records is
        # done by the rest of the domain
        parent_ids = OrderedSet()
        try:
            comodel.mapped(parent)
        except MissingError:
            comodel = comodel.exists()
        while comodel:
            parent_ids.update(comodel._ids)
            comodel = comodel[parent].filtered(lambda p: p.id not in parent_ids)
    return parent_ids