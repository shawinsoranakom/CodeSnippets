def native_value(self) -> StateType:
        """Return net spent+earned value for this category in the period."""
        spent_items = self._category.attributes.spent or []
        earned_items = self._category.attributes.earned or []
        spent = sum(float(item.sum) for item in spent_items if item.sum is not None)
        earned = sum(float(item.sum) for item in earned_items if item.sum is not None)
        if spent == 0 and earned == 0:
            return None
        return spent + earned