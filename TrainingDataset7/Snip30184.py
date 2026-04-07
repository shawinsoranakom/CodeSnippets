def traverse_qs(cls, obj_iter, path):
        """
        Helper method that returns a list containing a list of the objects in
        the obj_iter. Then for each object in the obj_iter, the path will be
        recursively travelled and the found objects are added to the return
        value.
        """
        ret_val = []

        if hasattr(obj_iter, "all"):
            obj_iter = obj_iter.all()

        try:
            iter(obj_iter)
        except TypeError:
            obj_iter = [obj_iter]

        for obj in obj_iter:
            rel_objs = []
            for part in path:
                if not part:
                    continue
                try:
                    related = getattr(obj, part[0])
                except ObjectDoesNotExist:
                    continue
                if related is not None:
                    rel_objs.extend(cls.traverse_qs(related, [part[1:]]))
            ret_val.append((obj, rel_objs))
        return ret_val