def get_candidate_relations_to_delete(opts):
    # The candidate relations are the ones that come from N-1 and 1-1
    # relations. N-N  (i.e., many-to-many) relations aren't candidates for
    # deletion.
    return (
        f
        for f in opts.get_fields(include_hidden=True)
        if f.auto_created and not f.concrete and (f.one_to_one or f.one_to_many)
    )