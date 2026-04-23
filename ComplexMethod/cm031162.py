def getElementById(self, id):
        if id in self._id_cache:
            return self._id_cache[id]
        if not (self._elem_info or self._magic_id_count):
            return None

        stack = self._id_search_stack
        if stack is None:
            # we never searched before, or the cache has been cleared
            stack = [self.documentElement]
            self._id_search_stack = stack
        elif not stack:
            # Previous search was completed and cache is still valid;
            # no matching node.
            return None

        result = None
        while stack:
            node = stack.pop()
            # add child elements to stack for continued searching
            stack.extend([child for child in node.childNodes
                          if child.nodeType in _nodeTypes_with_children])
            # check this node
            info = self._get_elem_info(node)
            if info:
                # We have to process all ID attributes before
                # returning in order to get all the attributes set to
                # be IDs using Element.setIdAttribute*().
                for attr in node.attributes.values():
                    if attr.namespaceURI:
                        if info.isIdNS(attr.namespaceURI, attr.localName):
                            self._id_cache[attr.value] = node
                            if attr.value == id:
                                result = node
                            elif not node._magic_id_nodes:
                                break
                    elif info.isId(attr.name):
                        self._id_cache[attr.value] = node
                        if attr.value == id:
                            result = node
                        elif not node._magic_id_nodes:
                            break
                    elif attr._is_id:
                        self._id_cache[attr.value] = node
                        if attr.value == id:
                            result = node
                        elif node._magic_id_nodes == 1:
                            break
            elif node._magic_id_nodes:
                for attr in node.attributes.values():
                    if attr._is_id:
                        self._id_cache[attr.value] = node
                        if attr.value == id:
                            result = node
            if result is not None:
                break
        return result