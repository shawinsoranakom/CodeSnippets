def docclass(self, object, name=None, mod=None, funcs={}, classes={},
                 *ignored):
        """Produce HTML documentation for a class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        contents = []
        push = contents.append

        # Cute little class to pump out a horizontal rule between sections.
        class HorizontalRule:
            def __init__(self):
                self.needone = 0
            def maybe(self):
                if self.needone:
                    push('<hr>\n')
                self.needone = 1
        hr = HorizontalRule()

        # List the mro, if non-trivial.
        mro = deque(inspect.getmro(object))
        if len(mro) > 2:
            hr.maybe()
            push('<dl><dt>Method resolution order:</dt>\n')
            for base in mro:
                push('<dd>%s</dd>\n' % self.classlink(base,
                                                      object.__module__))
            push('</dl>\n')

        def spill(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    try:
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self.docdata(value, name, mod))
                    else:
                        push(self.document(value, name, mod,
                                        funcs, classes, mdict, object, homecls))
                    push('\n')
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self.docdata(value, name, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = _split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    base = self.docother(getattr(object, name), name, mod)
                    doc = getdoc(value)
                    if not doc:
                        push('<dl><dt>%s</dl>\n' % base)
                    else:
                        doc = self.markup(getdoc(value), self.preformat,
                                          funcs, classes, mdict)
                        doc = '<dd><span class="code">%s</span>' % doc
                        push('<dl><dt>%s%s</dl>\n' % (base, doc))
                    push('\n')
            return attrs

        attrs = [(name, kind, cls, value)
                 for name, kind, cls, value in classify_class_attrs(object)
                 if visiblename(name, obj=object)]

        mdict = {}
        for key, kind, homecls, value in attrs:
            mdict[key] = anchor = '#' + name + '-' + key
            try:
                value = getattr(object, name)
            except Exception:
                # Some descriptors may meet a failure in their __get__.
                # (bug #1785)
                pass
            try:
                # The value may not be hashable (e.g., a data attr with
                # a dict or list value).
                mdict[value] = anchor
            except TypeError:
                pass

        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = _split_list(attrs, lambda t: t[2] is thisclass)

            if object is not builtins.object and thisclass is builtins.object:
                attrs = inherited
                continue
            elif thisclass is object:
                tag = 'defined here'
            else:
                tag = 'inherited from %s' % self.classlink(thisclass,
                                                           object.__module__)
            tag += ':<br>\n'

            sort_attributes(attrs, object)

            # Pump out the attrs, segregated by kind.
            attrs = spill('Methods %s' % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill('Class methods %s' % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill('Static methods %s' % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("Readonly properties %s" % tag, attrs,
                                     lambda t: t[1] == 'readonly property')
            attrs = spilldescriptors('Data descriptors %s' % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata('Data and other attributes %s' % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited

        contents = ''.join(contents)

        if name == realname:
            title = '<a name="%s">class <strong>%s</strong></a>' % (
                name, realname)
        else:
            title = '<strong>%s</strong> = <a name="%s">class %s</a>' % (
                name, name, realname)
        if bases:
            parents = []
            for base in bases:
                parents.append(self.classlink(base, object.__module__))
            title = title + '(%s)' % ', '.join(parents)

        decl = ''
        argspec = _getargspec(object)
        if argspec and argspec != '()':
            decl = name + self.escape(argspec) + '\n\n'

        doc = getdoc(object)
        if decl:
            doc = decl + (doc or '')
        doc = self.markup(doc, self.preformat, funcs, classes, mdict)
        doc = doc and '<span class="code">%s<br>&nbsp;</span>' % doc

        return self.section(title, 'title', contents, 3, doc)