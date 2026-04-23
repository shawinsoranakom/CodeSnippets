def __init__(self, related):
        # Following the example above, `related` is an instance of OneToOneRel
        # which represents the reverse restaurant field (place.restaurant).
        self.related = related