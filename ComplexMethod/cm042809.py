def merge_moov(moovs, mdats):
    mvhd_duration = 0
    for x in moovs:
        mvhd_duration += x.get(b'mvhd').get('duration')
    tkhd_durations = [0, 0]
    mdhd_durations = [0, 0]
    for x in moovs:
        traks = x.get_all(b'trak')
        assert len(traks) == 2
        tkhd_durations[0] += traks[0].get(b'tkhd').get('duration')
        tkhd_durations[1] += traks[1].get(b'tkhd').get('duration')
        mdhd_durations[0] += traks[0].get(b'mdia', b'mdhd').get('duration')
        mdhd_durations[1] += traks[1].get(b'mdia', b'mdhd').get('duration')
    #mvhd_duration = min(mvhd_duration, tkhd_durations)

    trak0s = [x.get_all(b'trak')[0] for x in moovs]
    trak1s = [x.get_all(b'trak')[1] for x in moovs]

    stts0 = merge_stts(x.get(b'mdia', b'minf', b'stbl', b'stts').body[1] for x in trak0s)
    stts1 = merge_stts(x.get(b'mdia', b'minf', b'stbl', b'stts').body[1] for x in trak1s)

    stss = merge_stss((x.get(b'mdia', b'minf', b'stbl', b'stss').body[1] for x in trak0s), (len(x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3]) for x in trak0s))

    stsc0 = merge_stsc((x.get(b'mdia', b'minf', b'stbl', b'stsc').body[1] for x in trak0s), (len(x.get(b'mdia', b'minf', b'stbl', b'stco').body[1]) for x in trak0s))
    stsc1 = merge_stsc((x.get(b'mdia', b'minf', b'stbl', b'stsc').body[1] for x in trak1s), (len(x.get(b'mdia', b'minf', b'stbl', b'stco').body[1]) for x in trak1s))

    stco0 = merge_stco((x.get(b'mdia', b'minf', b'stbl', b'stco').body[1] for x in trak0s), mdats)
    stco1 = merge_stco((x.get(b'mdia', b'minf', b'stbl', b'stco').body[1] for x in trak1s), mdats)

    stsz0 = merge_stsz((x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3] for x in trak0s))
    stsz1 = merge_stsz((x.get(b'mdia', b'minf', b'stbl', b'stsz').body[3] for x in trak1s))

    ctts = sum((x.get(b'mdia', b'minf', b'stbl', b'ctts').body[1] for x in trak0s), [])

    moov = moovs[0]

    moov.get(b'mvhd').set('duration', mvhd_duration)
    trak0 = moov.get_all(b'trak')[0]
    trak1 = moov.get_all(b'trak')[1]
    trak0.get(b'tkhd').set('duration', tkhd_durations[0])
    trak1.get(b'tkhd').set('duration', tkhd_durations[1])
    trak0.get(b'mdia', b'mdhd').set('duration', mdhd_durations[0])
    trak1.get(b'mdia', b'mdhd').set('duration', mdhd_durations[1])

    stts_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stts')
    stts_atom.body = stts_atom.body[0], stts0
    stts_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stts')
    stts_atom.body = stts_atom.body[0], stts1

    stss_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stss')
    stss_atom.body = stss_atom.body[0], stss

    stsc_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stsc')
    stsc_atom.body = stsc_atom.body[0], stsc0
    stsc_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stsc')
    stsc_atom.body = stsc_atom.body[0], stsc1

    stco_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco0
    stco_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco1

    stsz_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stsz')
    stsz_atom.body = stsz_atom.body[0], stsz_atom.body[1], len(stsz0), stsz0
    stsz_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stsz')
    stsz_atom.body = stsz_atom.body[0], stsz_atom.body[1], len(stsz1), stsz1

    ctts_atom = trak0.get(b'mdia', b'minf', b'stbl', b'ctts')
    ctts_atom.body = ctts_atom.body[0], ctts

    old_moov_size = moov.size
    new_moov_size = moov.calsize()
    new_mdat_start = mdats[0].body[1] + new_moov_size - old_moov_size
    stco0 = list(map(lambda x: x + new_mdat_start, stco0))
    stco1 = list(map(lambda x: x + new_mdat_start, stco1))
    stco_atom = trak0.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco0
    stco_atom = trak1.get(b'mdia', b'minf', b'stbl', b'stco')
    stco_atom.body = stss_atom.body[0], stco1

    return moov