def check_proxy(proxies, return_ip=False):
    """
    检查代理配置并返回结果。

    Args:
        proxies (dict): 包含http和https代理配置的字典。
        return_ip (bool, optional): 是否返回代理的IP地址。默认为False。

    Returns:
        str or None: 检查的结果信息或代理的IP地址（如果`return_ip`为True）。
    """
    import requests
    proxies_https = proxies['https'] if proxies is not None else '无'
    ip = None
    try:
        response = requests.get("https://ipapi.co/json/", proxies=proxies, timeout=4)  # ⭐ 执行GET请求以获取代理信息
        data = response.json()
        if 'country_name' in data:
            country = data['country_name']
            result = f"代理配置 {proxies_https}, 代理所在地：{country}"
            if 'ip' in data:
                ip = data['ip']
        elif 'error' in data:
            alternative, ip = _check_with_backup_source(proxies)  # ⭐ 调用备用方法检查代理配置
            if alternative is None:
                result = f"代理配置 {proxies_https}, 代理所在地：未知，IP查询频率受限"
            else:
                result = f"代理配置 {proxies_https}, 代理所在地：{alternative}"
        else:
            result = f"代理配置 {proxies_https}, 代理数据解析失败：{data}"

        if not return_ip:
            logger.warning(result)
            return result
        else:
            return ip
    except:
        result = f"代理配置 {proxies_https}, 代理所在地查询超时，代理可能无效"
        if not return_ip:
            logger.warning(result)
            return result
        else:
            return ip