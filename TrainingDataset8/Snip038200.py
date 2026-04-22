def __eq__(self, other: object) -> bool:
        if not isinstance(other, UploadedFile):
            return NotImplemented
        return self.id == other.id