def __and__(self, other: SetExpression) -> Union:
        assert isinstance(other, Union)
        if self.is_universal():
            return other
        if other.is_universal():
            return self
        if self.is_empty() or other.is_empty():
            return EMPTY_UNION
        if self == other:
            return self
        return Union(
            self_inter & other_inter
            for self_inter in self.__inters
            for other_inter in other.__inters
        )