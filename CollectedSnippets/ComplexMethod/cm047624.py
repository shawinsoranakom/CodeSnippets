def _optimize_step(self, model: BaseModel, level: OptimizationLevel) -> Domain:
        # optimize children
        children = self._flatten(child._optimize(model, level) for child in self.children)
        size = len(children)
        if size > 1:
            # sort children in order to ease their grouping by field and operator
            children.sort(key=_optimize_nary_sort_key)
            # run optimizations until some merge happens
            cls = type(self)
            for merge in _MERGE_OPTIMIZATIONS:
                children = merge(cls, children, model)
                if len(children) < size:
                    break
            else:
                # if no change, skip creation of a new object
                if len(self.children) == len(children) and all(map(operator.is_, self.children, children)):
                    return self
        return self.apply(children)