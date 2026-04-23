def flatten(flight_data):
            if not isinstance(flight_data, list):
                return
            if len(flight_data) == 4 and flight_data[0] == '$':
                _, name, _, data = flight_data
                if not isinstance(data, dict):
                    return
                children = data.pop('children', None)
                if data and isinstance(name, str) and re.fullmatch(r'\$L[0-9a-f]+', name):
                    # It is useful hydration JSON data
                    nextjs_data[name[2:]] = data
                flatten(children)
                return
            for f in flight_data:
                flatten(f)