def coolness(self, instance):
        if instance.pk:
            return "%s amount of cool." % instance.pk
        else:
            return "Unknown coolness."