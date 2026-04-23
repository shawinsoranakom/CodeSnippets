def _process_single_offline_gemm(untuned_gemm_line: str, gpu_id: int) -> None:
    r"""Process a single untuned GEMM."""

    deviceid = "cuda:" + str(gpu_id)

    dtype_dict = {
        "float": torch.float32,
        "tf32": torch.float32,
        "double": torch.float64,
        "BFloat16": torch.bfloat16,
        "Half": torch.half,
        "c10::complex<double>": torch.complex128,
        "c10::complex<float>": torch.complex64,
        "Float8_e4m3fn": torch.float8_e4m3fn,
        "Float8_e5m2": torch.float8_e5m2,
        "Float8_e4m3fnuz": torch.float8_e4m3fnuz,
        "Float8_e5m2fnuz": torch.float8_e5m2fnuz,
    }

    untuned_gemm = untuned_gemm_line.strip().split(",")[:]

    underscore_count = untuned_gemm[0].count("_")

    # Initialize dtype to make linter happy
    dtype = None
    dtypeA = None
    dtypeB = None
    dtypeC = None

    # Extract BLAS parameters
    if underscore_count == 2:
        [op_sig, data_type, layout] = untuned_gemm[0].split("_")
        transB = layout[0] == "T"
        transA = layout[1] == "T"
        dtype = dtype_dict.get(data_type)
        if data_type == "tf32":
            torch.backends.cuda.matmul.allow_tf32 = True
        else:
            torch.backends.cuda.matmul.allow_tf32 = False

    else:  # ScaledGEMM
        count = untuned_gemm[0].count("_")
        if count not in [6, 7]:
            raise AssertionError(f"count must be 6 or 7, got {count}")
        untuned_gemm_temp = untuned_gemm[0].split("_")
        # dtypeC = might not be FP8 type, keep track
        # of the number of underscores
        op_sig = untuned_gemm_temp[0]
        data_typeA = untuned_gemm_temp[1] + "_" + untuned_gemm_temp[2]
        data_typeB = untuned_gemm_temp[3] + "_" + untuned_gemm_temp[4]
        if count == 7:
            data_typeC = untuned_gemm_temp[5] + "_" + untuned_gemm_temp[6]
        else:
            data_typeC = untuned_gemm_temp[5]
        transB = untuned_gemm_temp[count][0] == "T"
        transA = untuned_gemm_temp[count][1] == "T"
        dtypeA = dtype_dict.get(data_typeA)
        dtypeB = dtype_dict.get(data_typeB)
        dtypeC = dtype_dict.get(data_typeC)

    untuned_gemm_temp = untuned_gemm[1].split("_")
    [n, m, k] = [int(g) for g in untuned_gemm_temp[1:4]]
    if op_sig == "GemmStridedBatchedTunableOp":
        if untuned_gemm_temp[6] != "ld":
            raise AssertionError(
                f"expected 'ld' at index 6, got {untuned_gemm_temp[6]!r}"
            )
        [ldb, lda, ldc] = [int(g) for g in untuned_gemm_temp[7:10]]
    else:
        if untuned_gemm_temp[4] != "ld":
            raise AssertionError(
                f"expected 'ld' at index 4, got {untuned_gemm_temp[4]!r}"
            )
        [ldb, lda, ldc] = [int(g) for g in untuned_gemm_temp[5:8]]

    # Detect subMatrix case
    if all(item in [n, m, k] for item in [lda, ldb, ldc]):
        subMatrix = False
    else:
        subMatrix = True

    if op_sig == "GemmTunableOp":
        # Warnings for unsupported cases:
        if m == 1 or n == 1 or k == 1:
            if (not transA) and (not transB):
                pass  # case is supported
            elif transA and n == 1:
                pass  # case is supported
            else:
                warnings.warn(
                    "Offline tuning is not supported for this GEMM. Use online tuning instead. "
                    + f"Skipped tuning for: {untuned_gemm[1]}",
                    stacklevel=2,
                )
                return

        # Resolve linter issue
        if dtype is None or not isinstance(dtype, torch.dtype):
            raise TypeError(f"dtype must be a torch.dtype, but got {dtype}")

        matA, matB = _create_matrices(
            m, n, k, lda, ldb, ldc, transA, transB, dtype, deviceid, subMatrix=subMatrix
        )
        torch.mm(matA, matB)

    elif op_sig == "GemmStridedBatchedTunableOp":
        # Warnings for unsupported cases:
        if m == 1 or n == 1 or k == 1:
            warnings.warn(
                "Offline tuning is not support for this GEMM. Use online tuning instead. "
                + f"Skipped tuning for: {untuned_gemm[1]}",
                stacklevel=2,
            )
            return

        [b] = [int(g) for g in untuned_gemm_temp[5:6]]

        # Resolve linter issue
        if dtype is None or not isinstance(dtype, torch.dtype):
            raise TypeError(f"dtype must be a torch.dtype, but got {dtype}")

        matA, matB = _create_batch_matrices(
            m,
            n,
            k,
            b,
            lda,
            ldb,
            ldc,
            transA,
            transB,
            dtype,
            deviceid,
            subMatrix=subMatrix,
        )
        torch.bmm(matA, matB)
    elif op_sig == "ScaledGemmTunableOp":
        # Only combination supported by PyTorch
        if transB is not True:
            raise AssertionError(
                f"transB must be True for ScaledGemmTunableOp, got {transB}"
            )
        if transA is not False:
            raise AssertionError(
                f"transA must be False for ScaledGemmTunableOp, got {transA}"
            )

        # Resolve linter issue
        if dtypeA is None or not isinstance(dtypeA, torch.dtype):
            raise TypeError(f"dtype must be a torch.dtype, but got {dtypeA}")

        matA, matB = _create_matrices(
            m,
            n,
            k,
            lda,
            ldb,
            ldc,
            transA,
            transB,
            dtypeA,
            deviceid,
            dtypeB=dtypeB,
            randn=False,
            subMatrix=subMatrix,
        )

        if untuned_gemm_temp[8] != "rw":
            raise AssertionError(
                f"expected 'rw' at index 8, got {untuned_gemm_temp[8]!r}"
            )
        if untuned_gemm_temp[9] == "1":
            rowwise = True
        else:
            rowwise = False
        if rowwise:
            scaleA = (
                torch.ones((1, m), device=deviceid)
                if transA
                else torch.ones((m, 1), device=deviceid)
            )
            scaleB = (
                torch.ones((1, n), device=deviceid)
                if transB
                else torch.ones((n, 1), device=deviceid)
            )
        else:
            scaleA = torch.tensor(0.8, device=deviceid)
            scaleB = torch.tensor(0.9, device=deviceid)

        if untuned_gemm_temp[10] != "bias":
            raise AssertionError(
                f"expected 'bias' at index 10, got {untuned_gemm_temp[10]!r}"
            )
        if untuned_gemm_temp[11] == "None":  # no bias vector
            torch._scaled_mm(
                matA, matB, scale_a=scaleA, scale_b=scaleB, out_dtype=dtypeC
            )
        else:  # bias vector present
            fillbias = 0.10
            bias_dtype = dtype_dict.get(untuned_gemm_temp[11])
            bias = (
                torch.full((n,), fillbias, dtype=bias_dtype, device=deviceid)
                if transB
                else torch.full((m,), fillbias, dtype=bias_dtype, device=deviceid)
            )
            torch._scaled_mm(
                matA, matB, scale_a=scaleA, scale_b=scaleB, out_dtype=dtypeC, bias=bias
            )

    elif op_sig == "GemmAndBiasTunableOp":
        # y = x*A^T + b
        if transA == transB:
            raise AssertionError(
                f"transA and transB must differ for GemmAndBiasTunableOp, got transA={transA}, transB={transB}"
            )

        # Resolve linter issue
        if dtype is None or not isinstance(dtype, torch.dtype):
            raise TypeError(f"dtype must be a torch.dtype, but got {dtype}")

        bias = torch.rand(n, dtype=dtype, device=deviceid)

        X, matA = _create_matrices(
            m, n, k, lda, ldb, ldc, transA, transB, dtype, deviceid, subMatrix=subMatrix
        )
        matA = matA.t()
        torch.nn.functional.linear(X, matA, bias)
    else:
        warnings.warn(f"error: unknown op {op_sig}", stacklevel=2)