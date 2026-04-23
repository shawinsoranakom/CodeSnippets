def docmodule(self, object, name=None, mod=None, *ignored):
        """Produce HTML documentation for a module object."""
        name = object.__name__ # ignore the passed-in name
        try:
            all = object.__all__
        except AttributeError:
            all = None
        parts = name.split('.')
        links = []
        for i in range(len(parts)-1):
            links.append(
                '<a href="%s.html" class="white">%s</a>' %
                ('.'.join(parts[:i+1]), parts[i]))
        linkedname = '.'.join(links + parts[-1:])
        head = '<strong class="title">%s</strong>' % linkedname
        try:
            path = inspect.getabsfile(object)
            url = urllib.parse.quote(path)
            filelink = self.filelink(url, path)
        except TypeError:
            filelink = '(built-in)'
        info = []

        if version := self._get_version(object):
            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            info.append('version %s' % self.escape(version))
        if hasattr(object, '__date__'):
            info.append(self.escape(str(object.__date__)))
        if info:
            head = head + ' (%s)' % ', '.join(info)
        docloc = self.getdocloc(object)
        if docloc is not None:
            docloc = '<br><a href="%(docloc)s">Module Reference</a>' % locals()
        else:
            docloc = ''
        result = self.heading(head, '<a href=".">index</a><br>' + filelink + docloc)

        modules = inspect.getmembers(object, inspect.ismodule)

        classes, cdict = [], {}
        for key, value in inspect.getmembers(object, inspect.isclass):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None or
                (inspect.getmodule(value) or object) is object):
                if visiblename(key, all, object):
                    classes.append((key, value))
                    cdict[key] = cdict[value] = '#' + key
        for key, value in classes:
            for base in value.__bases__:
                key, modname = base.__name__, base.__module__
                module = sys.modules.get(modname)
                if modname != name and module and hasattr(module, key):
                    if getattr(module, key) is base:
                        if not key in cdict:
                            cdict[key] = cdict[base] = modname + '.html#' + key
        funcs, fdict = [], {}
        for key, value in inspect.getmembers(object, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use a heuristic.
            if (all is not None
                or inspect.isbuiltin(value)
                or (inspect.getmodule(value) or object) is object):
                if visiblename(key, all, object):
                    funcs.append((key, value))
                    fdict[key] = '#-' + key
                    if inspect.isfunction(value): fdict[value] = fdict[key]
        data = []
        for key, value in inspect.getmembers(object, isdata):
            if visiblename(key, all, object):
                data.append((key, value))

        doc = self.markup(getdoc(object), self.preformat, fdict, cdict)
        doc = doc and '<span class="code">%s</span>' % doc
        result = result + '<p>%s</p>\n' % doc

        if hasattr(object, '__path__'):
            modpkgs = []
            for importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
                modpkgs.append((modname, name, ispkg, 0))
            modpkgs.sort()
            contents = self.multicolumn(modpkgs, self.modpkglink)
            result = result + self.bigsection(
                'Package Contents', 'pkg-content', contents)
        elif modules:
            contents = self.multicolumn(
                modules, lambda t: self.modulelink(t[1]))
            result = result + self.bigsection(
                'Modules', 'pkg-content', contents)

        if classes:
            classlist = [value for (key, value) in classes]
            contents = [
                self.formattree(inspect.getclasstree(classlist, 1), name)]
            for key, value in classes:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Classes', 'index', ' '.join(contents))
        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Functions', 'functions', ' '.join(contents))
        if data:
            contents = []
            for key, value in data:
                contents.append(self.document(value, key))
            result = result + self.bigsection(
                'Data', 'data', '<br>\n'.join(contents))
        if hasattr(object, '__author__'):
            contents = self.markup(str(object.__author__), self.preformat)
            result = result + self.bigsection('Author', 'author', contents)
        if hasattr(object, '__credits__'):
            contents = self.markup(str(object.__credits__), self.preformat)
            result = result + self.bigsection('Credits', 'credits', contents)

        return result