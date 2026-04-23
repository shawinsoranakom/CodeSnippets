def _get_keywords_docs(keys):

        data = {}
        descs = DocCLI._list_keywords()
        for key in keys:

            if key.startswith('with_'):
                # simplify loops, dont want to handle every with_<lookup> combo
                keyword = 'loop'
            elif key == 'async':
                # cause async became reserved in python we had to rename internally
                keyword = 'async_val'
            else:
                keyword = key

            try:
                # if no desc, typeerror raised ends this block
                kdata = {'description': descs[key]}

                # get playbook objects for keyword and use first to get keyword attributes
                kdata['applies_to'] = []
                for pobj in PB_OBJECTS:
                    if pobj not in PB_LOADED:
                        obj_class = 'ansible.playbook.%s' % pobj.lower()
                        loaded_class = importlib.import_module(obj_class)
                        PB_LOADED[pobj] = getattr(loaded_class, pobj, None)

                    if keyword in PB_LOADED[pobj].fattributes:
                        kdata['applies_to'].append(pobj)

                        # we should only need these once
                        if 'type' not in kdata:

                            fa = PB_LOADED[pobj].fattributes.get(keyword)
                            if getattr(fa, 'private'):
                                kdata = {}
                                raise KeyError

                            kdata['type'] = getattr(fa, 'isa', 'string')

                            if keyword.endswith('when') or keyword in ('until',):
                                # TODO: make this a field attribute property,
                                # would also helps with the warnings on {{}} stacking
                                kdata['template'] = 'implicit'
                            elif getattr(fa, 'static'):
                                kdata['template'] = 'static'
                            else:
                                kdata['template'] = 'explicit'

                            # those that require no processing
                            for visible in ('alias', 'priority'):
                                kdata[visible] = getattr(fa, visible)

                # remove None keys
                for k in list(kdata.keys()):
                    if kdata[k] is None:
                        del kdata[k]

                data[key] = kdata

            except (AttributeError, KeyError) as ex:
                display.error_as_warning(f'Skipping invalid keyword {key!r}.', ex)

        return data