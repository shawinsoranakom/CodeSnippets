def __init__(self, cls, doc=None, modulename="", func_doc=FunctionDoc, config=None):
        if not inspect.isclass(cls) and cls is not None:
            raise ValueError(f"Expected a class or None, but got {cls!r}")
        self._cls = cls

        if "sphinx" in sys.modules:
            from sphinx.ext.autodoc import ALL
        else:
            ALL = object()

        if config is None:
            config = {}
        self.show_inherited_members = config.get("show_inherited_class_members", True)

        if modulename and not modulename.endswith("."):
            modulename += "."
        self._mod = modulename

        if doc is None:
            if cls is None:
                raise ValueError("No class or documentation string given")
            doc = pydoc.getdoc(cls)

        NumpyDocString.__init__(self, doc)

        _members = config.get("members", [])
        if _members is ALL:
            _members = None
        _exclude = config.get("exclude-members", [])

        if config.get("show_class_members", True) and _exclude is not ALL:

            def splitlines_x(s):
                if not s:
                    return []
                else:
                    return s.splitlines()

            for field, items in [
                ("Methods", self.methods),
                ("Attributes", self.properties),
            ]:
                if not self[field]:
                    doc_list = []
                    for name in sorted(items):
                        if name in _exclude or (_members and name not in _members):
                            continue
                        try:
                            doc_item = pydoc.getdoc(getattr(self._cls, name))
                            doc_list.append(Parameter(name, "", splitlines_x(doc_item)))
                        except AttributeError:
                            pass  # method doesn't exist
                    self[field] = doc_list