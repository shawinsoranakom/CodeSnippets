def _start(self, tag, attrs, new_namespaces, qname_text=None):
        if self._exclude_attrs is not None and attrs:
            attrs = {k: v for k, v in attrs.items() if k not in self._exclude_attrs}

        qnames = {tag, *attrs}
        resolved_names = {}

        # Resolve prefixes in attribute and tag text.
        if qname_text is not None:
            qname = resolved_names[qname_text] = self._resolve_prefix_name(qname_text)
            qnames.add(qname)
        if self._find_qname_aware_attrs is not None and attrs:
            qattrs = self._find_qname_aware_attrs(attrs)
            if qattrs:
                for attr_name in qattrs:
                    value = attrs[attr_name]
                    if _looks_like_prefix_name(value):
                        qname = resolved_names[value] = self._resolve_prefix_name(value)
                        qnames.add(qname)
            else:
                qattrs = None
        else:
            qattrs = None

        # Assign prefixes in lexicographical order of used URIs.
        parse_qname = self._qname
        parsed_qnames = {n: parse_qname(n) for n in sorted(
            qnames, key=lambda n: n.split('}', 1))}

        # Write namespace declarations in prefix order ...
        if new_namespaces:
            attr_list = [
                ('xmlns:' + prefix if prefix else 'xmlns', uri)
                for uri, prefix in new_namespaces
            ]
            attr_list.sort()
        else:
            # almost always empty
            attr_list = []

        # ... followed by attributes in URI+name order
        if attrs:
            for k, v in sorted(attrs.items()):
                if qattrs is not None and k in qattrs and v in resolved_names:
                    v = parsed_qnames[resolved_names[v]][0]
                attr_qname, attr_name, uri = parsed_qnames[k]
                # No prefix for attributes in default ('') namespace.
                attr_list.append((attr_qname if uri else attr_name, v))

        # Honour xml:space attributes.
        space_behaviour = attrs.get('{http://www.w3.org/XML/1998/namespace}space')
        self._preserve_space.append(
            space_behaviour == 'preserve' if space_behaviour
            else self._preserve_space[-1])

        # Write the tag.
        write = self._write
        write('<' + parsed_qnames[tag][0])
        if attr_list:
            write(''.join([f' {k}="{_escape_attrib_c14n(v)}"' for k, v in attr_list]))
        write('>')

        # Write the resolved qname text content.
        if qname_text is not None:
            write(_escape_cdata_c14n(parsed_qnames[resolved_names[qname_text]][0]))

        self._root_seen = True
        self._ns_stack.append([])