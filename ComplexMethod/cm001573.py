def backcompat(d):
    """Checks infotext Version field, and enables backwards compatibility options according to it."""

    if not shared.opts.auto_backcompat:
        return

    ver = parse_version(d.get("Version"))
    if ver is None:
        return

    if ver < v160 and '[' in d.get('Prompt', ''):
        d["Old prompt editing timelines"] = True

    if ver < v160 and d.get('Sampler', '') in ('DDIM', 'PLMS'):
        d["Pad conds v0"] = True

    if ver < v170_tsnr:
        d["Downcast alphas_cumprod"] = True

    if ver < v180 and d.get('Refiner'):
        d["Refiner switch by sampling steps"] = True