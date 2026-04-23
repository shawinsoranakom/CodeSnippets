def __contains__(self, val):
        if not isinstance(val, Integral) and np.isnan(val):
            return False

        left_cmp = operator.lt if self.closed in ("left", "both") else operator.le
        right_cmp = operator.gt if self.closed in ("right", "both") else operator.ge

        left = -np.inf if self.left is None else self.left
        right = np.inf if self.right is None else self.right

        if left_cmp(val, left):
            return False
        if right_cmp(val, right):
            return False
        return True