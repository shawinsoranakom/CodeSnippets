def __str__(self):
        group_name = self.group.name if self.group_id else "NULL"
        return "%s is a member of %s" % (self.person.name, group_name)