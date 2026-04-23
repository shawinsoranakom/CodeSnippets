def add_fragments(doc, filename, fragment_loader, is_module=False, section='DOCUMENTATION'):

    if section not in _FRAGMENTABLE:
        raise AnsibleError(f"Invalid fragment section ({section}) passed to render {filename}, it can only be one of {_FRAGMENTABLE!r}")

    fragments = doc.pop('extends_documentation_fragment', [])

    if isinstance(fragments, str):
        fragments = fragments.split(',')

    unknown_fragments = []

    # doc_fragments are allowed to specify a fragment var other than DOCUMENTATION or RETURN
    # with a . separator; this is complicated by collections-hosted doc_fragments that
    # use the same separator. Assume it's collection-hosted normally first, try to load
    # as-specified. If failure, assume the right-most component is a var, split it off,
    # and retry the load.
    for fragment_slug in fragments:
        fragment_name = fragment_slug.strip()
        fragment_var = section

        fragment_class = fragment_loader.get(fragment_name)
        if fragment_class is None and '.' in fragment_slug:
            splitname = fragment_slug.rsplit('.', 1)
            fragment_name = splitname[0]
            fragment_var = splitname[1].upper()
            fragment_class = fragment_loader.get(fragment_name)

        if fragment_class is None:
            unknown_fragments.append(fragment_slug)
            continue

        # trust-tagged source propagates to loaded values; expressions and templates in config require trust
        fragment_yaml = _tags.TrustedAsTemplate().tag(getattr(fragment_class, fragment_var, None))
        if fragment_yaml is None:
            if fragment_var not in _FRAGMENTABLE:
                # if it's asking for something specific that's missing, that's an error
                unknown_fragments.append(fragment_slug)
                continue
            else:
                fragment_yaml = '{}'  # TODO: this is still an error later since we require 'options' below...

        fragment = yaml.load(_tags.Origin(path=filename).tag(fragment_yaml), Loader=AnsibleLoader)

        real_fragment_name = getattr(fragment_class, 'ansible_name')
        real_collection_name = '.'.join(real_fragment_name.split('.')[0:2]) if '.' in real_fragment_name else ''
        add_collection_to_versions_and_dates(fragment, real_collection_name, is_module=is_module, return_docs=(section == 'RETURN'))

        if section == 'DOCUMENTATION':
            # notes, seealso, options and attributes entries are specifically merged, but only occur in documentation section
            for doc_key in ['notes', 'seealso']:
                if doc_key in fragment:
                    entries = fragment.pop(doc_key)
                    if entries:
                        if doc_key not in doc:
                            doc[doc_key] = []
                        doc[doc_key].extend(entries)

            if 'options' not in fragment and 'attributes' not in fragment:
                raise AnsibleFragmentError("missing options or attributes in fragment (%s), possibly misformatted?: %s" % (fragment_name, filename))

            # ensure options themselves are directly merged
            for doc_key in ['options', 'attributes']:
                if doc_key in fragment:
                    if doc_key in doc:
                        try:
                            merge_fragment(doc[doc_key], fragment.pop(doc_key))
                        except Exception as e:
                            raise AnsibleFragmentError("%s %s (%s) of unknown type: %s" % (to_native(e), doc_key, fragment_name, filename))
                    else:
                        doc[doc_key] = fragment.pop(doc_key)

        # merge rest of the sections
        try:
            merge_fragment(doc, fragment)
        except Exception as e:
            raise AnsibleFragmentError("%s (%s) of unknown type: %s" % (to_native(e), fragment_name, filename))

    if unknown_fragments:
        raise AnsibleFragmentError('unknown doc_fragment(s) in file {0}: {1}'.format(filename, to_native(', '.join(unknown_fragments))))