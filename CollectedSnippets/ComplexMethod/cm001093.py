def send_side_effect(*args, **kwargs):
                data = kwargs.get("data", [])
                if isinstance(data, list) and len(data) == 1:
                    # Track which notification based on content
                    for i, notif in enumerate(notifications):
                        if any(
                            f"Test Agent {i}" in str(n.data)
                            for n in data
                            if hasattr(n, "data")
                        ):
                            # Index 1 has generic API error
                            if i == 1:
                                failed_indices.append(i)
                                raise Exception("Network timeout - temporary failure")
                            else:
                                successful_indices.append(i)
                                return None
                    return None
                # Force single processing
                raise Exception("Force single processing")