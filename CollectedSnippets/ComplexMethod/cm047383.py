def _combine(self, hierarchy: dict):
        """
        Return self's arch combined with its inherited views archs.

        :param hierarchy: mapping from parent views to their child views
        :return: combined architecture
        :rtype: Element
        """
        self.ensure_one()
        assert self.mode == 'primary'

        # We achieve a pre-order depth-first hierarchy traversal where
        # primary views (and their children) are traversed after all the
        # extensions for the current primary view have been visited.
        #
        # https://en.wikipedia.org/wiki/Tree_traversal#Depth-first_search_of_binary_tree
        #
        # Example:                  hierarchy = {
        #                               1: [2, 3],  # primary view
        #             1*                2: [4, 5],
        #            / \                3: [],
        #           2   3               4: [6],     # primary view
        #          / \                  5: [7, 8],
        #         4*  5                 6: [],
        #        /   / \                7: [],
        #       6   7   8               8: [],
        #                           }
        #
        # Tree traversal order (`view` and `queue` at the `while` stmt):
        #   1 [2, 3]
        #   2 [5, 3, 4]
        #   5 [7, 8, 3, 4]
        #   7 [8, 3, 4]
        #   8 [3, 4]
        #   3 [4]
        #   4 [6]
        #   6 []
        combined_arch = etree.fromstring(self.arch)
        if self.env.context.get('inherit_branding'):
            combined_arch.attrib.update({
                'data-oe-model': 'ir.ui.view',
                'data-oe-id': str(self.id),
                'data-oe-field': 'arch',
            })
        self._add_validation_flag(combined_arch)

        # The depth-first traversal is implemented with a double-ended queue.
        # The queue is traversed from left to right, and after each view in the
        # queue is processed, its children are pushed at the left of the queue,
        # so that they are traversed in order.  The queue is therefore mostly
        # used as a stack.  An exception is made for primary views, which are
        # pushed at the other end of the queue, so that they are applied after
        # all extensions have been applied.
        queue = collections.deque(sorted(hierarchy[self], key=lambda v: v.mode))
        tree_cut_off_view = self.env.context.get("ir_ui_view_tree_cut_off_view")
        while queue:
            view = queue.popleft()
            if view == tree_cut_off_view:
                break
            arch = etree.fromstring(view.arch or '<data/>')
            if view.env.context.get('inherit_branding'):
                view.inherit_branding(arch)
            self._add_validation_flag(combined_arch, view, arch)
            combined_arch = view.apply_inheritance_specs(combined_arch, arch)

            for child_view in reversed(hierarchy[view]):
                if child_view.mode == 'primary':
                    queue.append(child_view)
                else:
                    queue.appendleft(child_view)

        return combined_arch