def _match_func(info_dict, incomplete=False):
        ret = breaking_filters(info_dict, incomplete)
        if ret is not None:
            raise RejectedVideoReached(ret)

        if not filters or any(match_str(f, info_dict, incomplete) for f in filters):
            return NO_DEFAULT if interactive and not incomplete else None
        else:
            video_title = info_dict.get('title') or info_dict.get('id') or 'entry'
            filter_str = ') | ('.join(map(str.strip, filters))
            return f'{video_title} does not pass filter ({filter_str}), skipping ..'