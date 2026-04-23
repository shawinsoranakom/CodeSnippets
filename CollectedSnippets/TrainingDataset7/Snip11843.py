def all(self):
        # We can't proxy this method through the `QuerySet` like we do for the
        # rest of the `QuerySet` methods. This is because `QuerySet.all()`
        # works by creating a "copy" of the current queryset and in making said
        # copy, all the cached `prefetch_related` lookups are lost. See the
        # implementation of `RelatedManager.get_queryset()` for a better
        # understanding of how this comes into play.
        return self.get_queryset()