def GET(self):
        return QueryDict(self.META["QUERY_STRING"])