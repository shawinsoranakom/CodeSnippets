def make_module(self, name, pathentry=None, text=None):
        if text:
            text = dedent(text)
        if pathentry is None:
            pathentry = self.temp_dir()
        else:
            os.makedirs(pathentry, exist_ok=True)
        *subnames, basename = name.split('.')

        dirname = pathentry
        for subname in subnames:
            dirname = os.path.join(dirname, subname)
            if os.path.isdir(dirname):
                pass
            elif os.path.exists(dirname):
                raise Exception(dirname)
            else:
                os.mkdir(dirname)
            initfile = os.path.join(dirname, '__init__.py')
            if not os.path.exists(initfile):
                with open(initfile, 'w'):
                    pass
        filename = os.path.join(dirname, basename + '.py')

        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(text or '')
        return filename