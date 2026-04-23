def __str__(self):
        return "%s - %s" % (self.left.category.name, self.right.category.name)