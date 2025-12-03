class LookupService(object):

    def __init__(self):
        self.lookup = {}  

    def get_person(self, person_id):
        person_server = self.lookup[person_id]
        return person_server.people[person_id]
