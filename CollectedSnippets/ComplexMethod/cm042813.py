def get_resource_info(resource_url, client_id):
    cont = get_content(resource_url, decoded=True)

    x = re.escape('forEach(function(e){n(e)})}catch(e){}})},')
    x = re.search(r'' + x + r'(.*)\);</script>', cont)

    info = json.loads(x.group(1))[-1]['data'][0]

    info = info['tracks'] if info.get('track_count') else [info]

    ids = [i['id'] for i in info if i.get('comment_count') is None]
    ids = list(map(str, ids))
    ids_split = ['%2C'.join(ids[i:i+10]) for i in range(0, len(ids), 10)]
    api_url = 'https://api-v2.soundcloud.com/tracks?ids={ids}&client_id={client_id}&%5Bobject%20Object%5D=&app_version=1584348206&app_locale=en'

    res = []
    for ids in ids_split:
        uri = api_url.format(ids=ids, client_id=client_id)
        cont = get_content(uri, decoded=True)
        res += json.loads(cont)

    res = iter(res)
    info = [next(res) if i.get('comment_count') is None else i for i in info]

    return info