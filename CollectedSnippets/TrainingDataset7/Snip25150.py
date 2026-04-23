def patchGettextFind(self):
        gettext_module.find = lambda *args, **kw: None