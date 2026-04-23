def docroutine(self, object, name=None, mod=None, cl=None, homecls=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        if homecls is None:
            homecls = cl
        note = ''
        skipdocs = False
        imfunc = None
        if _is_bound_method(object):
            imself = object.__self__
            if imself is cl:
                imfunc = getattr(object, '__func__', None)
            elif inspect.isclass(imself):
                note = ' class method of %s' % classname(imself, mod)
            else:
                note = ' method of %s instance' % classname(
                    imself.__class__, mod)
        elif (inspect.ismethoddescriptor(object) or
              inspect.ismethodwrapper(object)):
            try:
                objclass = object.__objclass__
            except AttributeError:
                pass
            else:
                if cl is None:
                    note = ' unbound %s method' % classname(objclass, mod)
                elif objclass is not homecls:
                    note = ' from ' + classname(objclass, mod)
        else:
            imfunc = object
        if inspect.isfunction(imfunc) and homecls is not None and (
            imfunc.__module__ != homecls.__module__ or
            imfunc.__qualname__ != homecls.__qualname__ + '.' + realname):
            pname = parentname(imfunc, mod)
            if pname:
                note = ' from %s' % pname

        if (inspect.iscoroutinefunction(object) or
                inspect.isasyncgenfunction(object)):
            asyncqualifier = 'async '
        else:
            asyncqualifier = ''

        if name == realname:
            title = self.bold(realname)
        else:
            if (cl is not None and
                inspect.getattr_static(cl, realname, []) is object):
                skipdocs = True
                if note.startswith(' from '):
                    note = ''
            title = self.bold(name) + ' = ' + realname
        argspec = None

        if inspect.isroutine(object):
            argspec = _getargspec(object)
            if argspec and realname == '<lambda>':
                title = self.bold(name) + ' lambda '
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                if not object.__annotations__:
                    argspec = argspec[1:-1]
        if not argspec:
            argspec = '(...)'
        decl = asyncqualifier + title + argspec + note

        if skipdocs:
            return decl + '\n'
        else:
            doc = getdoc(object) or ''
            return decl + '\n' + (doc and self.indent(doc).rstrip() + '\n')