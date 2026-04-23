def _count(self, element, count=True):
        if not isinstance(element, str) and self == element:
            return 1
        if isinstance(element, RootElement) and self.children == element.children:
            return 1
        i = 0
        elem_child_idx = 0
        for child in self.children:
            # child is text content and element is also text content, then
            # make a simple "text" in "text"
            if isinstance(child, str):
                if isinstance(element, str):
                    if count:
                        i += child.count(element)
                    elif element in child:
                        return 1
            else:
                # Look for element wholly within this child.
                i += child._count(element, count=count)
                if not count and i:
                    return i
                # Also look for a sequence of element's children among self's
                # children. self.children == element.children is tested above,
                # but will fail if self has additional children. Ex: '<a/><b/>'
                # is contained in '<a/><b/><c/>'.
                if isinstance(element, RootElement) and element.children:
                    elem_child = element.children[elem_child_idx]
                    # Start or continue match, advance index.
                    if elem_child == child:
                        elem_child_idx += 1
                        # Match found, reset index.
                        if elem_child_idx == len(element.children):
                            i += 1
                            elem_child_idx = 0
                    # No match, reset index.
                    else:
                        elem_child_idx = 0
        return i