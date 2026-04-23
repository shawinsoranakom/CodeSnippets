def invert_intersect(self, factor: SetExpression) -> Union | None:
        """ Performs the inverse operation of intersection (a sort of factorization)
        such that: ``self == result & factor``.
        """
        if factor == self:
            return UNIVERSAL_UNION

        rfactor = ~factor
        if rfactor.is_empty() or rfactor.is_universal():
            return None
        rself = ~self

        assert isinstance(rfactor, Union)
        inters = [inter for inter in rself.__inters if inter not in rfactor.__inters]
        if len(rself.__inters) - len(inters) != len(rfactor.__inters):
            # not possible to invert the intersection
            return None

        rself_value = Union(inters)
        return ~rself_value