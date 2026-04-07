def __repr__(self):
        return "<Page %s of %s>" % (self.number, self.paginator.num_pages)