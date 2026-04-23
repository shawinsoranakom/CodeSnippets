def _preload_trees(self, refs: Sequence[int | str]):
        """ Preload all tree and subtree (from t-call and other '_get_preload_attribute_xmlids' values).

            Returns::

                {
                    id or xmlId/key: {
                        'xmlid': str | None,
                        'ref': int | None,
                        'tree': etree | None,
                        'template': str | None,
                        'error': None | MissingError
                    }
                }
        """
        compile_batch = self.env['ir.ui.view']._preload_views(refs)

        refs = list(map(_id_or_xmlid, refs))
        missing_refs = {ref: compile_batch[ref] for ref in refs if 'template' not in compile_batch[ref] and not compile_batch[ref]['error']}
        if not missing_refs:
            return compile_batch

        xmlids = list(missing_refs)
        missing_refs_values = list(missing_refs.values())
        views = self.env['ir.ui.view'].sudo().union(*[data['view'] for data in missing_refs_values])

        trees = views._get_view_etrees()

        # add in cache
        for xmlid, view, tree in zip(xmlids, views, trees):
            data = {
                'tree': tree,
                'template': etree.tostring(tree, encoding='unicode'),
            }
            compile_batch[view.id].update(data)
            compile_batch[xmlid].update(data)

        # preload sub template
        ref_names = self._get_preload_attribute_xmlids()
        sub_refs = OrderedSet()
        for tree in trees:
            sub_refs.update(
                el.get(ref_name)
                for ref_name in ref_names
                for el in tree.xpath(f'//*[@{ref_name}]')
                if not any(att.startswith('t-options-') or att == 't-options' or att == 't-lang' for att in el.attrib)
                if '{' not in el.get(ref_name) and '<' not in el.get(ref_name) and '/' not in el.get(ref_name)
            )
        assert not any(not f for f in sub_refs), "template is required"
        self._preload_trees(list(sub_refs))

        # not found template
        for ref in missing_refs:
            if ref not in compile_batch:
                compile_batch[ref] = {
                    'xmlid': ref,
                    'ref': ref,
                    'error': MissingError(self.env._("External ID can not be loaded: %s", ref)),
                }

        return compile_batch