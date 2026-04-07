def remove(self, *objs, bulk=True):
            if not objs:
                return
            self._clear(self.filter(pk__in=[o.pk for o in objs]), bulk)