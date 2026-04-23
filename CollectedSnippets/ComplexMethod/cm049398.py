def check_network(host=None):
    host = host or get_gateway()
    if not host:
        return None

    try:
        host = socket.gethostbyname(host)
    except socket.gaierror:
        return "unreachable"
    packet_loss, avg_latency = mtr(host)
    thresholds = {"fast": 5, "normal": 20} if ip_address(host).is_private else {"fast": 50, "normal": 150}

    if packet_loss is None or packet_loss >= 50 or avg_latency is None:
        return "unreachable"
    if avg_latency < thresholds["fast"] and packet_loss < 1:
        return "fast"
    if avg_latency < thresholds["normal"] and packet_loss < 5:
        return "normal"
    return "slow"