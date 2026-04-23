def receive_data_chunk(self, raw_data, start):
        """
        Receive data from the streamed upload parser. ``start`` is the position
        in the file of the chunk.
        """
        raise NotImplementedError(
            "subclasses of FileUploadHandler must provide a receive_data_chunk() method"
        )