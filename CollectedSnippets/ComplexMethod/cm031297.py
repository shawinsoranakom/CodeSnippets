async def _sock_sendfile_native(self, sock, file, offset, count):
        try:
            fileno = file.fileno()
        except (AttributeError, io.UnsupportedOperation):
            raise exceptions.SendfileNotAvailableError("not a regular file")
        try:
            fsize = os.fstat(fileno).st_size
        except OSError:
            raise exceptions.SendfileNotAvailableError("not a regular file")
        blocksize = count if count else fsize
        if not blocksize:
            return 0  # empty file

        blocksize = min(blocksize, 0xffff_ffff)
        end_pos = min(offset + count, fsize) if count else fsize
        offset = min(offset, fsize)
        total_sent = 0
        try:
            while True:
                blocksize = min(end_pos - offset, blocksize)
                if blocksize <= 0:
                    return total_sent
                await self._proactor.sendfile(sock, file, offset, blocksize)
                offset += blocksize
                total_sent += blocksize
        finally:
            if total_sent > 0:
                file.seek(offset)