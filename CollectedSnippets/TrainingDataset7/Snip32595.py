def items(self, obj):
        return Article.objects.filter(entry=obj)