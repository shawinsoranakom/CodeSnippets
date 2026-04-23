def __call__(self, path=None, path_args=None, **kw):
        path_prefix = path or self.path
        path = ''
        for key, value in self.args.items():
            kw.setdefault(key, value)
        slug = request.env['ir.http']._slug
        path_args = OrderedSet(path_args or []) | self.path_args
        paths, fragments = {}, []
        for key, value in kw.items():
            if value and key in path_args:
                if isinstance(value, models.BaseModel):
                    paths[key] = slug(value)
                else:
                    paths[key] = "%s" % value
            elif value:
                if isinstance(value, (list, set)):
                    fragments.append(urllib.parse.urlencode([(key, item) for item in value if item]))
                else:
                    fragments.append(urllib.parse.urlencode([(key, value)]))
        for key in path_args:
            value = paths.get(key)
            if value is not None:
                path += '/' + key + '/' + value
        if fragments:
            path += '?' + '&'.join(fragments)
        if not path.startswith(path_prefix):
            path = path_prefix + path
        return path