def compare_objects(gpu_obj, cpu_obj, path=""):
        # If objects are tensors, compare them
        if isinstance(gpu_obj, torch.Tensor) and isinstance(cpu_obj, torch.Tensor):
            # Check if devices are as expected
            if gpu_obj.device.type != device_type:
                return (
                    False,
                    f"Expected accelerator tensor, got {gpu_obj.device.type} tensor at {path}",
                )
            if cpu_obj.device.type != "cpu":
                return (
                    False,
                    f"Expected CPU tensor, got {cpu_obj.device.type} tensor at {path}",
                )
            if gpu_obj.storage_offset() != cpu_obj.storage_offset():
                return (
                    False,
                    f"Storage offset mismatch at {path}: {gpu_obj.storage_offset()} vs {cpu_obj.storage_offset()}",
                )

            if not torch.equal(gpu_obj.cpu(), cpu_obj):
                return (
                    False,
                    f"Tensors are not same at {path}",
                )

            # Track storage sharing
            gpu_storage_ptr = gpu_obj.storage().data_ptr()
            cpu_storage_ptr = cpu_obj.storage().data_ptr()

            if gpu_storage_ptr in gpu_storage_ptrs:
                # This GPU tensor shares storage with another tensor
                # Check if the corresponding CPU tensors also share storage
                if cpu_storage_ptr != gpu_storage_ptrs[gpu_storage_ptr]:
                    return (
                        False,
                        f"Storage sharing mismatch: GPU tensors share storage but CPU tensors don't at {path}",
                    )
            else:
                # First time seeing this storage
                gpu_storage_ptrs[gpu_storage_ptr] = cpu_storage_ptr
                cpu_storage_ptrs[cpu_storage_ptr] = gpu_storage_ptr

            return True, ""

        # If objects are dictionaries, compare them recursively
        elif isinstance(gpu_obj, dict) and isinstance(cpu_obj, dict):
            if gpu_obj.keys() != cpu_obj.keys():
                return (
                    False,
                    f"Dictionary keys mismatch at {path}: {gpu_obj.keys()} vs {cpu_obj.keys()}",
                )

            for key in gpu_obj:
                result, error = compare_objects(
                    gpu_obj[key], cpu_obj[key], f"{path}.{key}" if path else key
                )
                if not result:
                    return False, error

            return True, ""

        # If objects are lists, tuples, or sets, compare them recursively
        elif isinstance(gpu_obj, (list, tuple, set)) and isinstance(
            cpu_obj, (list, tuple, set)
        ):
            if len(gpu_obj) != len(cpu_obj):
                return (
                    False,
                    f"Collection length mismatch at {path}: {len(gpu_obj)} vs {len(cpu_obj)}",
                )
            if type(gpu_obj) is not type(cpu_obj):
                return (
                    False,
                    f"Collection type mismatch at {path}: {type(gpu_obj)} vs {type(cpu_obj)}",
                )

            for i, (gpu_item, cpu_item) in enumerate(zip(gpu_obj, cpu_obj)):
                result, error = compare_objects(gpu_item, cpu_item, f"{path}[{i}]")
                if not result:
                    return False, error

            return True, ""

        # If objects are custom classes, compare their attributes
        elif hasattr(gpu_obj, "__dict__") and hasattr(cpu_obj, "__dict__"):
            if type(gpu_obj) is not type(cpu_obj):
                return (
                    False,
                    f"Object type mismatch at {path}: {type(gpu_obj)} vs {type(cpu_obj)}",
                )

            result, error = compare_objects(
                gpu_obj.__dict__, cpu_obj.__dict__, f"{path}.__dict__"
            )
            if not result:
                return False, error

            return True, ""

        # For other types, use direct equality comparison
        else:
            if type(gpu_obj) is not type(cpu_obj):
                return (
                    False,
                    f"Type mismatch at {path}: {type(gpu_obj)} vs {type(cpu_obj)}",
                )
            if gpu_obj != cpu_obj:
                return False, f"Value mismatch at {path}: {gpu_obj} vs {cpu_obj}"

            return True, ""