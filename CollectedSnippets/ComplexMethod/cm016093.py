def output_json(filename, headers, row):
    """
    Write the result into JSON format, so that it can be uploaded to the benchmark database
    to be displayed on OSS dashboard. The JSON format is defined at
    https://github.com/pytorch/pytorch/wiki/How-to-integrate-with-PyTorch-OSS-benchmark-database
    """
    origin = ""
    if "torchbench" in filename:
        origin = "torchbench"
    elif "huggingface" in filename:
        origin = "huggingface"
    elif "timm_models" in filename:
        origin = "timm_models"

    extra_info = {
        "device": current_device,
        "quantization": current_quantization,
        "batch_size": current_batch_size,
    }
    if current_settings:
        extra_info.update(current_settings)

    mapping_headers = {headers[i]: v for i, v in enumerate(row)}
    with open(f"{os.path.splitext(filename)[0]}.json", "a") as f:
        for header, value in mapping_headers.items():
            # These headers are not metric names
            if header in ("dev", "name", "batch_size"):
                continue

            # Make sure that the record is valid
            if not current_name:
                continue

            record = {
                "benchmark": {
                    "name": "TorchInductor",
                    "mode": current_mode,
                    "dtype": current_dtype,
                    "extra_info": extra_info,
                },
                "model": {
                    "name": current_name,
                    "type": "OSS model",
                    "backend": current_backend,
                    "origins": [origin],
                },
            }

            # NB: When the metric is accuracy, its value is actually a string, i.e. pass, and
            # not a number. ClickHouse doesn't support mix types atm. It has a Variant type
            # https://clickhouse.com/docs/en/sql-reference/data-types/variant, but this isn't
            # recommended by CH team themselves. The workaround here is to store that value
            # in the extra_info field instead.
            if isinstance(value, str):
                record["metric"] = {
                    "name": header,
                    "extra_info": {"benchmark_values": [value]},
                }
            else:
                record["metric"] = {
                    "name": header,
                    "benchmark_values": [value],
                }

            print(json.dumps(record), file=f)