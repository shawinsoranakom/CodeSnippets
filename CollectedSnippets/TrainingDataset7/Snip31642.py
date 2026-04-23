def __str__(self):
        return "%s (%d) playing for %s" % (self.name, self.rank, self.team.to_string())