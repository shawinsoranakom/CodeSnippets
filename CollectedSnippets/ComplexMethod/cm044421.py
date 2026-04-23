def _write_zipfile(self, response: HTTPResponse, downloaded_size: int) -> None:
        """Write the model zip file to disk.

        Parameters
        ----------
        response
            The response from the model download task
        downloaded_size
            The amount of bytes downloaded so far
        """
        content_length = response.getheader("content-length")
        content_length = "0" if content_length is None else content_length
        length = int(content_length) + downloaded_size
        if length == downloaded_size:
            self.logger.info("Zip already exists. Skipping download")
            return
        write_type = "wb" if downloaded_size == 0 else "ab"
        assert tqdm is not None
        with open(self._model_zip_path, write_type) as out_file:
            p_bar = tqdm(desc="Downloading",
                         unit="B",
                         total=length,
                         unit_scale=True,
                         unit_divisor=1024)
            if downloaded_size != 0:
                p_bar.update(downloaded_size)
            while True:
                buffer = response.read(self._chunk_size)
                if not buffer:
                    break
                p_bar.update(len(buffer))
                out_file.write(buffer)
            p_bar.close()