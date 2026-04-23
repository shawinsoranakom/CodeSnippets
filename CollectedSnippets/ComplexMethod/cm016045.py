def identify_license(f, exception=''):
    """
    Read f and try to identify the license type
    This is __very__ rough and probably not legally binding, it is specific for
    this repo.
    """
    def squeeze(t):
        """Remove 'n and ' ', normalize quotes
        """
        t = t.replace('\n', '').replace(' ', '')
        t = t.replace('``', '"').replace("''", '"')
        return t

    with open(f) as fid:
        txt = fid.read()
        if not exception and 'exception' in txt:
            license = identify_license(f, 'exception')
            return license + ' with exception'
        txt = squeeze(txt)
        if 'ApacheLicense' in txt:
            # Hmm, do we need to check the text?
            return 'Apache-2.0'
        elif 'MITLicense' in txt:
            # Hmm, do we need to check the text?
            return 'MIT'
        elif 'BSD-3-ClauseLicense' in txt:
            # Hmm, do we need to check the text?
            return 'BSD-3-Clause'
        elif 'BSD3-ClauseLicense' in txt:
            # Hmm, do we need to check the text?
            return 'BSD-3-Clause'
        elif 'BoostSoftwareLicense-Version1.0' in txt:
            # Hmm, do we need to check the text?
            return 'BSL-1.0'
        elif squeeze("Clarified Artistic License") in txt:
            return 'Clarified Artistic License'
        elif all([squeeze(m) in txt.lower() for m in bsd3_txt]):
            return 'BSD-3-Clause'
        elif all([squeeze(m) in txt.lower() for m in bsd3_v1_txt]):
            return 'BSD-3-Clause'
        elif all([squeeze(m) in txt.lower() for m in bsd2_txt]):
            return 'BSD-2-Clause'
        elif all([squeeze(m) in txt.lower() for m in bsd3_src_txt]):
            return 'BSD-Source-Code'
        elif any([squeeze(m) in txt.lower() for m in mit_txt]):
            return 'MIT'
        else:
            raise ValueError('unknown license')