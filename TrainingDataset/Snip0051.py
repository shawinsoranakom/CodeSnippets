class UserGraphService(object):

    def __init__(self, person_ids, lookup):
        self.lookup = lookup
        self.person_ids = person_ids
        self.visited_ids = set()

