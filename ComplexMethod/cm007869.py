def establish_connection():
            ctx.chunk_size = (random.randint(int(chunk_size * 0.95), chunk_size)
                              if not is_test and chunk_size else chunk_size)
            if ctx.resume_len > 0:
                range_start = ctx.resume_len
                if ctx.is_resume:
                    self.report_resuming_byte(ctx.resume_len)
                ctx.open_mode = 'ab'
            elif ctx.chunk_size > 0:
                range_start = 0
            else:
                range_start = None
            ctx.is_resume = False
            range_end = range_start + ctx.chunk_size - 1 if ctx.chunk_size else None
            if range_end and ctx.data_len is not None and range_end >= ctx.data_len:
                range_end = ctx.data_len - 1
            has_range = range_start is not None
            ctx.has_range = has_range
            request = sanitized_Request(url, None, headers)
            if has_range:
                set_range(request, range_start, range_end)
            # Establish connection
            try:
                try:
                    ctx.data = self.ydl.urlopen(request)
                except (compat_urllib_error.URLError, ) as err:
                    # reason may not be available, e.g. for urllib2.HTTPError on python 2.6
                    reason = getattr(err, 'reason', None)
                    if isinstance(reason, socket.timeout):
                        raise RetryDownload(err)
                    raise err
                # When trying to resume, Content-Range HTTP header of response has to be checked
                # to match the value of requested Range HTTP header. This is due to webservers
                # that don't support resuming and serve a whole file with no Content-Range
                # set in response despite requested Range (see
                # https://github.com/ytdl-org/youtube-dl/issues/6057#issuecomment-126129799)
                if has_range:
                    content_range = ctx.data.headers.get('Content-Range')
                    if content_range:
                        content_range_m = re.search(r'bytes (\d+)-(\d+)?(?:/(\d+))?', content_range)
                        # Content-Range is present and matches requested Range, resume is possible
                        if content_range_m:
                            if range_start == int(content_range_m.group(1)):
                                content_range_end = int_or_none(content_range_m.group(2))
                                content_len = int_or_none(content_range_m.group(3))
                                accept_content_len = (
                                    # Non-chunked download
                                    not ctx.chunk_size
                                    # Chunked download and requested piece or
                                    # its part is promised to be served
                                    or content_range_end == range_end
                                    or content_len < range_end)
                                if accept_content_len:
                                    ctx.data_len = content_len
                                    return
                    # Content-Range is either not present or invalid. Assuming remote webserver is
                    # trying to send the whole file, resume is not possible, so wiping the local file
                    # and performing entire redownload
                    if range_start > 0:
                        self.report_unable_to_resume()
                    ctx.resume_len = 0
                    ctx.open_mode = 'wb'
                ctx.data_len = int_or_none(ctx.data.info().get('Content-length', None))
                return
            except (compat_urllib_error.HTTPError, ) as err:
                if err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    try:
                        # Open the connection again without the range header
                        ctx.data = self.ydl.urlopen(
                            sanitized_Request(url, None, headers))
                        content_length = ctx.data.info()['Content-Length']
                    except (compat_urllib_error.HTTPError, ) as err:
                        if err.code < 500 or err.code >= 600:
                            raise
                    else:
                        # Examine the reported length
                        if (content_length is not None
                                and (ctx.resume_len - 100 < int(content_length) < ctx.resume_len + 100)):
                            # The file had already been fully downloaded.
                            # Explanation to the above condition: in issue #175 it was revealed that
                            # YouTube sometimes adds or removes a few bytes from the end of the file,
                            # changing the file size slightly and causing problems for some users. So
                            # I decided to implement a suggested change and consider the file
                            # completely downloaded if the file size differs less than 100 bytes from
                            # the one in the hard drive.
                            self.report_file_already_downloaded(ctx.filename)
                            self.try_rename(ctx.tmpfilename, ctx.filename)
                            self._hook_progress({
                                'filename': ctx.filename,
                                'status': 'finished',
                                'downloaded_bytes': ctx.resume_len,
                                'total_bytes': ctx.resume_len,
                            })
                            raise SucceedDownload()
                        else:
                            # The length does not match, we start the download over
                            self.report_unable_to_resume()
                            ctx.resume_len = 0
                            ctx.open_mode = 'wb'
                            return
                elif err.code < 500 or err.code >= 600:
                    # Unexpected HTTP error
                    raise
                raise RetryDownload(err)
            except socket.error as err:
                if err.errno != errno.ECONNRESET:
                    # Connection reset is no problem, just retry
                    raise
                raise RetryDownload(err)