def gen_registration_headers(
    backend_index: BackendIndex,
    per_operator_headers: bool,
    rocm: bool,
) -> list[str]:
    if per_operator_headers:
        headers = ["#include <ATen/ops/as_strided_native.h>"]
    else:
        headers = ["#include <ATen/NativeFunctions.h>"]

    if backend_index.dispatch_key in (DispatchKey.CPU, DispatchKey.Meta):
        headers.append("#include <ATen/EmptyTensor.h>")
    elif backend_index.dispatch_key == DispatchKey.CUDA:
        if rocm:
            headers.append("#include <ATen/hip/EmptyTensor.h>")
        else:
            headers.append("#include <ATen/cuda/EmptyTensor.h>")
    elif backend_index.dispatch_key == DispatchKey.MPS:
        headers.append("#include <ATen/mps/EmptyTensor.h>")
    elif backend_index.dispatch_key == DispatchKey.XPU:
        # XPU specific, this header resides in third_party/torch-xpu-ops
        headers.append("#include <ATen/xpu/EmptyTensor.h>")
    elif backend_index.dispatch_key == DispatchKey.MTIA:
        headers.append("#include <ATen/native/mtia/EmptyTensor.h>")
    elif per_operator_headers:
        headers += [
            "#include <ATen/ops/empty.h>",
            "#include <ATen/ops/empty_strided.h>",
            "#include <ATen/ops/_copy_from_and_resize.h>",
            "#include <ATen/ops/_copy_from.h>",
        ]
    else:
        headers.append("#include <ATen/Functions.h>")

    headers.append("#include <c10/macros/Macros.h>")
    return headers