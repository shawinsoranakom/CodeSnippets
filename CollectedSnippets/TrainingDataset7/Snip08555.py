def from_dict(cls, file_dict):
        """
        Create a SimpleUploadedFile object from a dictionary with keys:
           - filename
           - content-type
           - content
        """
        return cls(
            file_dict["filename"],
            file_dict["content"],
            file_dict.get("content-type", "text/plain"),
        )