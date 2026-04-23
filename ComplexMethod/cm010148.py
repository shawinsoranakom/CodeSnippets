def rewrite(dim, item):
                # Redirect to torch.select for indexing.
                if item is None:
                    return dim + 1, (torch.unsqueeze, [dim])
                if isinstance(item, (int, torch.SymInt)):
                    return dim, (torch.select, [dim, item])
                # Redirect to torch.ops.aten.slice for slicing.
                if isinstance(item, slice):
                    step = item.step or 1
                    if item.start is None and item.stop is None and step == 1:
                        # no-op
                        return dim + 1, (lambda t: t, [])
                    return dim + 1, (
                        torch.ops.aten.slice,
                        [dim, item.start, item.stop, step],
                    )