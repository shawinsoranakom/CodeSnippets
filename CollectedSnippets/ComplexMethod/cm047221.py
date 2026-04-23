def parse_repr(self, group_repr):
        """ Return the group object from the string (given by the repr of the group object).

        :param group_repr: str
            Use | (union) and & (intersection) separator like the python object.
                intersection it's apply before union.
                Can use an invertion with ~.
        """
        if not group_repr:
            return self.definitions.universe
        res = None
        for union in group_repr.split('|'):
            union = union.strip()
            intersection = None
            if union.startswith('(') and union.endswith(')'):
                union = union[1:-1]
            for xmlid in union.split('&'):
                xmlid = xmlid.strip()
                leaf = ~self.definitions.parse(xmlid[1:]) if xmlid.startswith('~') else self.definitions.parse(xmlid)
                if intersection is None:
                    intersection = leaf
                else:
                    intersection &= leaf
            if intersection is None:
                return self.definitions.universe
            elif res is None:
                res = intersection
            else:
                res |= intersection
        return self.definitions.empty if res is None else res