def merge(*lists):
        """
        Merge lists while trying to keep the relative order of the elements.
        Warn if the lists have the same elements in a different relative order.

        For static assets it can be important to have them included in the DOM
        in a certain order. In JavaScript you may not be able to reference a
        global or in CSS you might want to override a style.
        """
        ts = TopologicalSorter()
        for head, *tail in filter(None, lists):
            ts.add(head)  # Ensure that the first items are included.
            for item in tail:
                if head != item:  # Avoid circular dependency to self.
                    ts.add(item, head)
                head = item
        try:
            return list(ts.static_order())
        except CycleError:
            warnings.warn(
                "Detected duplicate Media files in an opposite order: {}".format(
                    ", ".join(repr(list_) for list_ in lists)
                ),
                MediaOrderConflictWarning,
            )
            return list(dict.fromkeys(chain.from_iterable(filter(None, lists))))