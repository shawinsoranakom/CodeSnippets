def test_invalid_devices(self):
        if self.rank != 0:
            return
        dst_worker_name = dist_utils.worker_name((self.rank + 1) % self.world_size)

        with self.assertRaisesRegex(
            RuntimeError,
            r"Expected one of .+ device type at start of device string",
        ):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    f"{dst_worker_name}/foo",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        if TEST_WITH_ROCM:
            errorString = (
                r"HIP error: invalid device ordinal\n"
                r"HIP kernel errors might be asynchronously reported at some other API call, "
                r"so the stacktrace below might be incorrect.\n"
                r"For debugging consider passing AMD_SERIALIZE_KERNEL=3"
            )
        else:
            errorString = r"CUDA error: invalid device ordinal"
        with self.assertRaisesRegex(RuntimeError, errorString):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    f"{dst_worker_name}/cuda:100",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        with self.assertRaisesRegex(RuntimeError, r"Invalid device string: 'cpu2'"):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    f"{dst_worker_name}/cpu2",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        with self.assertRaisesRegex(RuntimeError, r"Device string must not be empty"):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    f"{dst_worker_name}/",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        with self.assertRaisesRegex(
            ValueError,
            r"Could not parse remote_device: worker1/cuda:0/cuda:1. The valid format is '<workername>/<device>'",
        ):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    f"{dst_worker_name}/cuda:0/cuda:1",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        with self.assertRaisesRegex(
            ValueError,
            r"Could not parse remote_device: /. The valid format is '<workername>/<device>'",
        ):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    "/",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]

        with self.assertRaisesRegex(
            ValueError,
            r"Could not parse remote_device: /cuda:0. The valid format is '<workername>/<device>'",
        ):
            [
                m.forward()
                for m in self._create_remote_module_iter(
                    "/cuda:0",
                    modes=[ModuleCreationMode.MODULE_CTOR],
                )
            ]