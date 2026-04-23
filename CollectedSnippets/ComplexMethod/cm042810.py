def concat_flv(flvs, output = None):
    assert flvs, 'no flv file found'
    import os.path
    if not output:
        output = guess_output(flvs)
    elif os.path.isdir(output):
        output = os.path.join(output, guess_output(flvs))

    print('Merging video parts...')
    ins = [open(flv, 'rb') for flv in flvs]
    for stream in ins:
        read_flv_header(stream)
    meta_tags = map(read_tag, ins)
    metas = list(map(read_meta_tag, meta_tags))
    meta_types, metas = zip(*metas)
    assert len(set(meta_types)) == 1
    meta_type = meta_types[0]

    # must merge fields: duration
    # TODO: check other meta info, update other meta info
    total_duration = sum(meta.get('duration') for meta in metas)
    meta_data = metas[0]
    meta_data.set('duration', total_duration)

    out = open(output, 'wb')
    write_flv_header(out)
    write_meta_tag(out, meta_type, meta_data)
    timestamp_start = 0
    for stream in ins:
        while True:
            tag = read_tag(stream)
            if tag:
                data_type, timestamp, body_size, body, previous_tag_size = tag
                timestamp += timestamp_start
                tag = data_type, timestamp, body_size, body, previous_tag_size
                write_tag(out, tag)
            else:
                break
        timestamp_start = timestamp
    write_uint(out, previous_tag_size)

    return output