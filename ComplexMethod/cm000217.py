def _bubble_down(self, elem: T) -> None:
        # Place a node at the proper position (downward movement) [to be used
        # internally only]
        curr_pos = self.position_map[elem]
        _, weight = self.heap[curr_pos]
        child_left_position = get_child_left_position(curr_pos)
        child_right_position = get_child_right_position(curr_pos)
        if child_left_position < self.elements and child_right_position < self.elements:
            _, child_left_weight = self.heap[child_left_position]
            _, child_right_weight = self.heap[child_right_position]
            if child_right_weight < child_left_weight and child_right_weight < weight:
                self._swap_nodes(child_right_position, curr_pos)
                return self._bubble_down(elem)
        if child_left_position < self.elements:
            _, child_left_weight = self.heap[child_left_position]
            if child_left_weight < weight:
                self._swap_nodes(child_left_position, curr_pos)
                return self._bubble_down(elem)
        else:
            return None
        if child_right_position < self.elements:
            _, child_right_weight = self.heap[child_right_position]
            if child_right_weight < weight:
                self._swap_nodes(child_right_position, curr_pos)
                return self._bubble_down(elem)
        return None