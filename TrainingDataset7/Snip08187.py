def item_link(self, item):
        try:
            return item.get_absolute_url()
        except AttributeError:
            raise ImproperlyConfigured(
                "Give your %s class a get_absolute_url() method, or define an "
                "item_link() method in your Feed class." % item.__class__.__name__
            )