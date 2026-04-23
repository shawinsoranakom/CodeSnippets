def docroutine(self, object, name=None, mod=None,
                   funcs={}, classes={}, methods={}, cl=None, homecls=None):
        """Produce HTML documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        if homecls is None:
            homecls = cl
        anchor = ('' if cl is None else cl.__name__) + '-' + name
        note = ''
        skipdocs = False
        imfunc = None
        if _is_bound_method(object):
            imself = object.__self__
            if imself is cl:
                imfunc = getattr(object, '__func__', None)
            elif inspect.isclass(imself):
                note = ' class method of %s' % self.classlink(imself, mod)
            else:
                note = ' method of %s instance' % self.classlink(
                    imself.__class__, mod)
        elif (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            try:
                objclass = object.__objclass__
            except AttributeError:
                pass
            else:
                if cl is None:
                    note = ' unbound %s method' % self.classlink(objclass, mod)
                elif objclass is not homecls:
                    note = ' from ' + self.classlink(objclass, mod)
        else:
            imfunc = object
        if inspect.isfunction(imfunc) and homecls is not None and (
            imfunc.__module__ != homecls.__module__ or
            imfunc.__qualname__ != homecls.__qualname__ + '.' + realname):
            pname = self.parentlink(imfunc, mod)
            if pname:
                note = ' from %s' % pname

        if (inspect.iscoroutinefunction(object) or
                inspect.isasyncgenfunction(object)):
            asyncqualifier = 'async '
        else:
            asyncqualifier = ''

        if name == realname:
            title = '<a name="%s"><strong>%s</strong></a>' % (anchor, realname)
        else:
            if (cl is not None and
                inspect.getattr_static(cl, realname, []) is object):
                reallink = '<a href="#%s">%s</a>' % (
                    cl.__name__ + '-' + realname, realname)
                skipdocs = True
                if note.startswith(' from '):
                    note = ''
            else:
                reallink = realname
            title = '<a name="%s"><strong>%s</strong></a> = %s' % (
                anchor, name, reallink)
        argspec = None
        if inspect.isroutine(object):
            argspec = _getargspec(object)
            if argspec and realname == '<lambda>':
                title = '<strong>%s</strong> <em>lambda</em> ' % name
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                if not object.__annotations__:
                    argspec = argspec[1:-1] # remove parentheses
        if not argspec:
            argspec = '(...)'

        decl = asyncqualifier + title + self.escape(argspec) + (note and
               self.grey('<span class="heading-text">%s</span>' % note))

        if skipdocs:
            return '<dl><dt>%s</dt></dl>\n' % decl
        else:
            doc = self.markup(
                getdoc(object), self.preformat, funcs, classes, methods)
            doc = doc and '<dd><span class="code">%s</span></dd>' % doc
            return '<dl><dt>%s</dt>%s</dl>\n' % (decl, doc)