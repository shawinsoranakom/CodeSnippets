def _make_pge_trace(
    collectives=None,
    matmuls=None,
    sdpa_ops=None,
    pg_config=None,
):
    """Build a minimal Chrome Trace JSON dict for PGE testing."""
    events = []
    eid = 1000

    for coll in collectives or []:
        events.append(
            {
                "cat": "kernel",
                "dur": coll["dur"],
                "name": "nccl_kernel",
                "args": {
                    "Collective name": coll["name"],
                    "Process Group Name": coll.get("pg_name", "0"),
                    "Process Group Ranks": coll.get("ranks", "[0, 1]"),
                    "Group size": coll.get("group_size", 2),
                    "In msg nelems": coll.get("nelems", 1024),
                    "Out msg nelems": coll.get("out_nelems", coll.get("nelems", 1024)),
                    "dtype": coll.get("dtype", "Float"),
                },
            }
        )

    for mm in matmuls or []:
        eid += 1
        events.append(
            {
                "cat": "cpu_op",
                "name": "aten::mm",
                "dur": 0,
                "args": {
                    "External id": eid,
                    "Input Dims": mm["shapes"],
                    "Input Strides": mm.get(
                        "strides", [[s[-1], 1] for s in mm["shapes"]]
                    ),
                    "Input type": mm.get("dtypes", ["float", "float"]),
                },
            }
        )
        events.append(
            {
                "cat": "kernel",
                "dur": mm["dur"],
                "name": "sm80_xmma_gemm",
                "args": {"External id": eid},
            }
        )

    for sdpa in sdpa_ops or []:
        eid += 1
        op_name = sdpa.get("op_name", "aten::_scaled_dot_product_flash_attention")
        events.append(
            {
                "cat": "cpu_op",
                "name": op_name,
                "dur": 0,
                "args": {
                    "External id": eid,
                    "Input Dims": sdpa["input_dims"],
                    "Input Strides": sdpa.get(
                        "input_strides", [[1] * len(d) for d in sdpa["input_dims"]]
                    ),
                    "Input type": sdpa.get("dtypes", ["c10::BFloat16"]),
                },
            }
        )
        events.append(
            {
                "cat": "kernel",
                "dur": sdpa["dur"],
                "name": "flash_fwd_kernel",
                "args": {"External id": eid},
            }
        )

    dist_info = {}
    if pg_config is not None:
        dist_info["pg_config"] = pg_config
    else:
        dist_info["pg_config"] = {"0": {"ranks": [0, 1]}}

    return {"traceEvents": events, "distributedInfo": dist_info}