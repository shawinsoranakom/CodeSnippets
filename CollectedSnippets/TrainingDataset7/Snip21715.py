def new_revision(self):
        new_revision = copy.copy(self)
        new_revision.pk = None
        return new_revision