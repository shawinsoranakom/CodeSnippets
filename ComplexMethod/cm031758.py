def write_pot_file(messages, options, fp):
    timestamp = time.strftime('%Y-%m-%d %H:%M%z')
    encoding = fp.encoding if fp.encoding else 'UTF-8'
    print(pot_header % {'time': timestamp, 'version': __version__,
                        'charset': encoding,
                        'encoding': '8bit'}, file=fp)

    # Sort locations within each message by filename and lineno
    sorted_keys = [
        (key, sorted(msg.locations))
        for key, msg in messages.items()
    ]
    # Sort messages by locations
    # For example, a message with locations [('test.py', 1), ('test.py', 2)] will
    # appear before a message with locations [('test.py', 1), ('test.py', 3)]
    sorted_keys.sort(key=itemgetter(1))

    for key, locations in sorted_keys:
        msg = messages[key]

        for comment in msg.comments:
            print(f'#. {comment}', file=fp)

        if options.writelocations:
            # location comments are different b/w Solaris and GNU:
            if options.locationstyle == options.SOLARIS:
                for location in locations:
                    print(f'# File: {location.filename}, line: {location.lineno}', file=fp)
            elif options.locationstyle == options.GNU:
                # fit as many locations on one line, as long as the
                # resulting line length doesn't exceed 'options.width'
                locline = '#:'
                for location in locations:
                    s = f' {location.filename}:{location.lineno}'
                    if len(locline) + len(s) <= options.width:
                        locline = locline + s
                    else:
                        print(locline, file=fp)
                        locline = f'#:{s}'
                if len(locline) > 2:
                    print(locline, file=fp)
        if msg.is_docstring:
            # If the entry was gleaned out of a docstring, then add a
            # comment stating so.  This is to aid translators who may wish
            # to skip translating some unimportant docstrings.
            print('#, docstring', file=fp)
        if msg.msgctxt is not None:
            print('msgctxt', normalize(msg.msgctxt, encoding), file=fp)
        print('msgid', normalize(msg.msgid, encoding), file=fp)
        if msg.msgid_plural is not None:
            print('msgid_plural', normalize(msg.msgid_plural, encoding), file=fp)
            print('msgstr[0] ""', file=fp)
            print('msgstr[1] ""\n', file=fp)
        else:
            print('msgstr ""\n', file=fp)