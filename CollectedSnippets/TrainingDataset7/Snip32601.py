def item_pubdate(self, item):
        # Provide a weird offset so that the test can know it's getting this
        # specific offset and not accidentally getting on from
        # settings.TIME_ZONE.
        return item.published.replace(tzinfo=get_fixed_timezone(42))