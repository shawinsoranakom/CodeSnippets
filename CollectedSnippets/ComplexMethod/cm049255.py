def filters_from_context():
            view_tree = None
            for key, value in context.items():
                if key.startswith('search_default_') and value:
                    filter_name = key[15:]
                    if not check_object_name(filter_name):
                        raise ValueError(model.env._("Invalid default search filter name for %s", key))
                    if view_tree is None:
                        view = model.get_view(action.search_view_id.id, 'search')
                        view_tree = etree.fromstring(view['arch'])
                    if (element := view_tree.find(Rf'.//filter[@name="{filter_name}"]')) is not None:
                        # parse the domain
                        if domain := element.attrib.get('domain'):
                            yield domain