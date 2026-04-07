def item_link(self, item):
        return "%sarticle/%s/" % (item.entry.get_absolute_url(), item.pk)