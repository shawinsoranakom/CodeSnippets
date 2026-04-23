def _normalize_proxy_config(value):
        """Normalize proxy_config to ProxyConfig, list of ProxyConfig/None, or None."""
        if isinstance(value, list):
            normalized = []
            for p in value:
                if p is None or p == "direct":
                    normalized.append(None)
                elif isinstance(p, dict):
                    normalized.append(ProxyConfig.from_dict(p))
                elif isinstance(p, str):
                    normalized.append(ProxyConfig.from_string(p))
                else:
                    normalized.append(p)
            return normalized
        elif isinstance(value, dict):
            return ProxyConfig.from_dict(value)
        elif isinstance(value, str):
            if value == "direct":
                return None
            return ProxyConfig.from_string(value)
        return value