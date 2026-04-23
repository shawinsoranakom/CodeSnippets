def url_save_icourses(url, filepath, bar, total_size, dyn_callback=None, is_part=False, max_size=0, headers=None):
    def dyn_update_url(received):
        if callable(dyn_callback):
            logging.debug('Calling callback %s for new URL from %s' % (dyn_callback.__name__, received))
            return dyn_callback(received)
    if bar is None:
        bar = DummyProgressBar()
    if os.path.exists(filepath):
        if not force:
            if not is_part:
                bar.done()
                print('Skipping %s: file already exists' % tr(os.path.basename(filepath)))
            else:
                filesize = os.path.getsize(filepath)
                bar.update_received(filesize)
            return
        else:
            if not is_part:
                bar.done()
                print('Overwriting %s' % os.path.basename(filepath), '...')
    elif not os.path.exists(os.path.dirname(filepath)):
        os.mkdir(os.path.dirname(filepath))

    temp_filepath = filepath + '.download'
    received = 0
    if not force:
        open_mode = 'ab'

        if os.path.exists(temp_filepath):
            tempfile_size = os.path.getsize(temp_filepath)
            received += tempfile_size
            bar.update_received(tempfile_size)
    else:
        open_mode = 'wb'

    if received:
        url = dyn_update_url(received)

    if headers is None:
        headers = {}
    response = urlopen_with_retry(request.Request(url, headers=headers))
# Do not update content-length here.
# Only the 1st segment's content-length is the content-length of the file.
# For other segments, content-length is the standard one, 15 * 1024 * 1024

    with open(temp_filepath, open_mode) as output:
        before_this_uri = received
# received - before_this_uri is size of the buf we get from one uri
        while True:
            update_bs = 256 * 1024
            left_bytes = total_size - received
            to_read = left_bytes if left_bytes <= update_bs else update_bs
# calc the block size to read -- The server can fail to send an EOF
            buffer = response.read(to_read)
            if not buffer:
                logging.debug('Got EOF from server')
                break
            output.write(buffer)
            received += len(buffer)
            bar.update_received(len(buffer))
            if received >= total_size:
                break
            if max_size and (received - before_this_uri) >= max_size:
                url = dyn_update_url(received)
                before_this_uri = received
                response = urlopen_with_retry(request.Request(url, headers=headers))

    assert received == os.path.getsize(temp_filepath), '%s == %s' % (received, os.path.getsize(temp_filepath))

    if os.access(filepath, os.W_OK):
        os.remove(filepath)  # on Windows rename could fail if destination filepath exists
    os.rename(temp_filepath, filepath)