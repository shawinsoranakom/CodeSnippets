class PersonServer(object):

    def __init__(self):
        self.people = {}  # key: person_id, value: person

    def get_people(self, ids):
        results = []
        for id in ids:
            if id in self.people:
                results.append(self.people[id])
        return results
