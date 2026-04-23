def download():
            data_len = ctx.data.headers.get('Content-length')

            if ctx.data.headers.get('Content-encoding'):
                # Content-encoding is present, Content-length is not reliable anymore as we are
                # doing auto decompression. (See: https://github.com/yt-dlp/yt-dlp/pull/6176)
                data_len = None

            # Range HTTP header may be ignored/unsupported by a webserver
            # (e.g. extractor/scivee.py, extractor/bambuser.py).
            # However, for a test we still would like to download just a piece of a file.
            # To achieve this we limit data_len to _TEST_FILE_SIZE and manually control
            # block size when downloading a file.
            if is_test and (data_len is None or int(data_len) > self._TEST_FILE_SIZE):
                data_len = self._TEST_FILE_SIZE

            if data_len is not None:
                data_len = int(data_len) + ctx.resume_len
                min_data_len = self.params.get('min_filesize')
                max_data_len = self.params.get('max_filesize')
                if min_data_len is not None and data_len < min_data_len:
                    self.to_screen(
                        f'\r[download] File is smaller than min-filesize ({data_len} bytes < {min_data_len} bytes). Aborting.')
                    return False
                if max_data_len is not None and data_len > max_data_len:
                    self.to_screen(
                        f'\r[download] File is larger than max-filesize ({data_len} bytes > {max_data_len} bytes). Aborting.')
                    return False

            byte_counter = 0 + ctx.resume_len
            block_size = ctx.block_size
            start = time.time()

            # measure time over whole while-loop, so slow_down() and best_block_size() work together properly
            now = None  # needed for slow_down() in the first loop run
            before = start  # start measuring

            def retry(e):
                close_stream()
                if ctx.tmpfilename == '-':
                    ctx.resume_len = byte_counter
                else:
                    try:
                        ctx.resume_len = os.path.getsize(ctx.tmpfilename)
                    except FileNotFoundError:
                        ctx.resume_len = 0
                raise RetryDownload(e)

            while True:
                try:
                    # Download and write
                    data_block = ctx.data.read(block_size if not is_test else min(block_size, data_len - byte_counter))
                except TransportError as err:
                    retry(err)

                byte_counter += len(data_block)

                # exit loop when download is finished
                if len(data_block) == 0:
                    break

                # Open destination file just in time
                if ctx.stream is None:
                    try:
                        ctx.stream, ctx.tmpfilename = self.sanitize_open(
                            ctx.tmpfilename, ctx.open_mode)
                        assert ctx.stream is not None
                        ctx.filename = self.undo_temp_name(ctx.tmpfilename)
                        self.report_destination(ctx.filename)
                    except OSError as err:
                        self.report_error(f'unable to open for writing: {err}')
                        return False

                try:
                    ctx.stream.write(data_block)
                except OSError as err:
                    self.to_stderr('\n')
                    self.report_error(f'unable to write data: {err}')
                    return False

                # Apply rate limit
                self.slow_down(start, now, byte_counter - ctx.resume_len)

                # end measuring of one loop run
                now = time.time()
                after = now

                # Adjust block size
                if not self.params.get('noresizebuffer', False):
                    block_size = self.best_block_size(after - before, len(data_block))

                before = after

                # Progress message
                speed = self.calc_speed(start, now, byte_counter - ctx.resume_len)
                if ctx.data_len is None:
                    eta = None
                else:
                    eta = self.calc_eta(start, time.time(), ctx.data_len - ctx.resume_len, byte_counter - ctx.resume_len)

                self._hook_progress({
                    'status': 'downloading',
                    'downloaded_bytes': byte_counter,
                    'total_bytes': ctx.data_len,
                    'tmpfilename': ctx.tmpfilename,
                    'filename': ctx.filename,
                    'eta': eta,
                    'speed': speed,
                    'elapsed': now - ctx.start_time,
                    'ctx_id': info_dict.get('ctx_id'),
                }, info_dict)

                if data_len is not None and byte_counter == data_len:
                    break

                if speed and speed < (self.params.get('throttledratelimit') or 0):
                    # The speed must stay below the limit for 3 seconds
                    # This prevents raising error when the speed temporarily goes down
                    if ctx.throttle_start is None:
                        ctx.throttle_start = now
                    elif now - ctx.throttle_start > 3:
                        if ctx.stream is not None and ctx.tmpfilename != '-':
                            ctx.stream.close()
                        raise ThrottledDownload
                elif speed:
                    ctx.throttle_start = None

            if ctx.stream is None:
                self.to_stderr('\n')
                self.report_error('Did not get any data blocks')
                return False

            if not is_test and ctx.chunk_size and ctx.content_len is not None and byte_counter < ctx.content_len:
                ctx.resume_len = byte_counter
                raise NextFragment

            if ctx.tmpfilename != '-':
                ctx.stream.close()

            if data_len is not None and byte_counter != data_len:
                err = ContentTooShortError(byte_counter, int(data_len))
                retry(err)

            self.try_rename(ctx.tmpfilename, ctx.filename)

            # Update file modification time
            if self.params.get('updatetime'):
                info_dict['filetime'] = self.try_utime(ctx.filename, ctx.data.headers.get('last-modified', None))

            self._hook_progress({
                'downloaded_bytes': byte_counter,
                'total_bytes': byte_counter,
                'filename': ctx.filename,
                'status': 'finished',
                'elapsed': time.time() - ctx.start_time,
                'ctx_id': info_dict.get('ctx_id'),
            }, info_dict)

            return True