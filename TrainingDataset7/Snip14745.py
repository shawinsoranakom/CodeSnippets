def create(cls, children=None, connector=None, negated=False):
        """
        Create a new instance using Node() instead of __init__() as some
        subclasses, e.g. django.db.models.query_utils.Q, may implement a custom
        __init__() with a signature that conflicts with the one defined in
        Node.__init__().
        """
        obj = Node(children, connector or cls.default, negated)
        obj.__class__ = cls
        return obj