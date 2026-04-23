def getdocloc(self, object, basedir=None):
        """Return the location of module docs or None"""
        basedir = self.STDLIB_DIR if basedir is None else basedir
        docloc = os.environ.get("PYTHONDOCS", self.PYTHONDOCS)

        if (self._is_stdlib_module(object, basedir) and
            object.__name__ not in ('xml.etree', 'test.test_pydoc.pydoc_mod')):

            try:
                from pydoc_data import module_docs
            except ImportError:
                module_docs = None

            if module_docs and object.__name__ in module_docs.module_docs:
                doc_name = module_docs.module_docs[object.__name__]
                if docloc.startswith(("http://", "https://")):
                    docloc = "{}/{}".format(docloc.rstrip("/"), doc_name)
                else:
                    docloc = os.path.join(docloc, doc_name)
            else:
                docloc = None
        else:
            docloc = None
        return docloc