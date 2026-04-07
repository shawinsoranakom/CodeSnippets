def is_local_storage(self):
        return isinstance(self.storage, FileSystemStorage)