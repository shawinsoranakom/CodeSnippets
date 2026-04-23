def _parse_path(cls, path):
        if not path:
            return '', '', []
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        if altsep:
            path = path.replace(altsep, sep)
        drv, root, rel = cls.parser.splitroot(path)
        if not root and drv.startswith(sep) and not drv.endswith(sep):
            drv_parts = drv.split(sep)
            if len(drv_parts) == 4 and drv_parts[2] not in '?.':
                # e.g. //server/share
                root = sep
            elif len(drv_parts) == 6:
                # e.g. //?/unc/server/share
                root = sep
        return drv, root, [x for x in rel.split(sep) if x and x != '.']