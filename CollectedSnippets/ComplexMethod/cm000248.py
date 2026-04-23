def update(
        self, idx: int, left_element: int, right_element: int, a: int, b: int, val: int
    ) -> bool:
        """
        update with O(lg n) (Normal segment tree without lazy update will take O(nlg n)
        for each update)

        update(1, 1, size, a, b, v) for update val v to [a,b]
        """
        if self.flag[idx] is True:
            self.segment_tree[idx] = self.lazy[idx]
            self.flag[idx] = False
            if left_element != right_element:
                self.lazy[self.left(idx)] = self.lazy[idx]
                self.lazy[self.right(idx)] = self.lazy[idx]
                self.flag[self.left(idx)] = True
                self.flag[self.right(idx)] = True

        if right_element < a or left_element > b:
            return True
        if left_element >= a and right_element <= b:
            self.segment_tree[idx] = val
            if left_element != right_element:
                self.lazy[self.left(idx)] = val
                self.lazy[self.right(idx)] = val
                self.flag[self.left(idx)] = True
                self.flag[self.right(idx)] = True
            return True
        mid = (left_element + right_element) // 2
        self.update(self.left(idx), left_element, mid, a, b, val)
        self.update(self.right(idx), mid + 1, right_element, a, b, val)
        self.segment_tree[idx] = max(
            self.segment_tree[self.left(idx)], self.segment_tree[self.right(idx)]
        )
        return True