def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        if self.fastupdate is not None:
            kwargs["fastupdate"] = self.fastupdate
        if self.gin_pending_list_limit is not None:
            kwargs["gin_pending_list_limit"] = self.gin_pending_list_limit
        return path, args, kwargs