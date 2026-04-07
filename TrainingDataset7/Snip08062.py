def paginator(self):
        return paginator.Paginator(self._items(), self.limit)