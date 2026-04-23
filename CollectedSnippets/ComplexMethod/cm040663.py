def model_supports_jit(model):
    # XLA not supported with TF on MacOS GPU
    if platform.system() == "Darwin" and "arm" in platform.processor().lower():
        if backend.backend() == "tensorflow":
            from keras.src.utils.module_utils import tensorflow as tf

            if tf.config.list_physical_devices("GPU"):
                return False
    # XLA not supported by some layers
    if all(x.supports_jit for x in model._flatten_layers()):
        if backend.backend() == "tensorflow":
            from tensorflow.python.framework.config import (
                is_op_determinism_enabled,
            )

            if is_op_determinism_enabled():
                # disable XLA with determinism enabled since not all ops are
                # supported by XLA with determinism enabled.
                return False
        return True
    return False