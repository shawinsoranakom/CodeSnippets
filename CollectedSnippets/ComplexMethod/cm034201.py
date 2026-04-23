def _build_doc(self, role, path, collection, argspec, entry_point):
        if collection:
            fqcn = '.'.join([collection, role])
        else:
            fqcn = role
        doc = {}
        doc['path'] = path
        doc['collection'] = collection
        if 'error' in argspec:
            doc.update(argspec)
        else:
            doc['entry_points'] = {}
            for ep in argspec.keys():
                if entry_point is None or ep == entry_point:
                    entry_spec = argspec[ep] or {}
                    doc['entry_points'][ep] = entry_spec

            # If we didn't add any entry points (b/c of filtering), ignore this entry.
            if len(doc['entry_points'].keys()) == 0:
                doc = None

        return (fqcn, doc)