def __str__(self):
        # This method intentionally doesn't work for all cases - part
        # of the test for ticket #20278
        return SelfRef.objects.get(selfref=self).pk