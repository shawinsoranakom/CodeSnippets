def __getstate__(self):
        obj_dict = self.__dict__.copy()
        obj_dict["querysets"] = []
        for queryset in self.querysets:
            if queryset is not None:
                queryset = queryset._chain()
                # Prevent the QuerySet from being evaluated
                queryset._result_cache = []
                queryset._prefetch_done = True
                obj_dict["querysets"].append(queryset)
        return obj_dict