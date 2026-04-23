def process_fields(fields: List[str]) -> List[Union[str, int]]:
    processed: List[Union[str, int]] = list(fields)
    current_timestamp = int(time.time() * 1000)

    for idx, typ in HASH_FIELDS.items():
        if idx >= len(processed):
            continue

        if typ == "split":
            # field 16: "count|hash" -> replace only hash
            val = str(processed[idx])
            parts = val.split("|")
            if len(parts) == 2:
                processed[idx] = f"{parts[0]}|{random_hash()}"
        elif typ == "full":
            if idx == 36:
                processed[idx] = random.randint(10, 100)  # 10-100
            else:
                processed[idx] = random_hash()

    # field 33: current timestamp
    if 33 < len(processed):
        processed[33] = current_timestamp

    return processed