def _compiled_and_package(
        self,
        f: torch.types.FileLike,
        standalone: bool = False,
        package_example_inputs: bool = False,
    ) -> None:
        options: dict[str, typing.Any] = {
            "aot_inductor.package": True,
            "aot_inductor.package_cpp_only": True,
            "always_keep_tensor_constants": True,
            # we'll change this back to False once we enable weight deduping for standalone mode
            "aot_inductor.package_constants_in_so": standalone,
            "aot_inductor_mode.compile_standalone": standalone,
        }
        aoti_files_map = {}
        model_names = []
        device_type = "cpu"
        for name, ep in self._method_overloads:
            name = name.replace(":", "__")
            model_names.append(name)
            options["aot_inductor.model_name_for_generated_files"] = name
            aoti_files = torch._inductor.aot_compile(
                ep.module(),  # type: ignore[arg-type]
                ep.example_inputs[0],
                kwargs=ep.example_inputs[1],
                options=options,
            )
            # pyrefly: ignore [unsupported-operation]
            aoti_files_map[name] = aoti_files

        from torch._inductor.package import package

        pt2_path = package.package_aoti(
            f,
            aoti_files_map,  # type: ignore[arg-type]
        )

        if not standalone:
            return

        if not isinstance(pt2_path, str):
            raise AssertionError(
                f"Expected pt2_path to be a string, but got {type(pt2_path)}"
            )
        base_directory = os.path.dirname(pt2_path)
        package_name = os.path.basename(pt2_path)[:-4]
        with zipfile.ZipFile(pt2_path, "r") as zip_ref:
            zip_ref.extractall(base_directory)

        example_inputs_map: dict[str, int] | None = (
            {} if package_example_inputs else None
        )
        for name, ep in self._method_overloads:
            name = name.replace(":", "__")
            # TODO: also dump kwargs
            # TODO: currently only support list of Tensors and they need to be on the same device
            if not ep.example_inputs:
                continue

            device_types: OrderedSet[str] = OrderedSet()

            for inp in ep.example_inputs[0]:
                if isinstance(inp, torch.Tensor):
                    device_types.add(inp.device.type)
            device_types.discard("cpu")
            if len(device_types) > 1:
                raise AssertionError(
                    "Does not support mixing {}".format("+".join(list(device_types)))
                )
            device_type = "cpu" if len(device_types) == 0 else device_types.pop()

            if package_example_inputs:
                if example_inputs_map is None:
                    raise AssertionError(
                        "example_inputs_map cannot be None when package_example_inputs is True"
                    )
                example_inputs_map[name] = len(ep.example_inputs[0])
                for i, t in enumerate(ep.example_inputs[0]):
                    path = Path(base_directory) / f"{name}_input_{i}.pt"
                    torch.save(t, path)

        cmake_file_str = _get_make_file(
            package_name, model_names, device_type=device_type
        )

        with open(Path(base_directory) / "CMakeLists.txt", "w") as file:
            file.write(cmake_file_str)

        main_file_str = _get_main_cpp_file(
            package_name, model_names, example_inputs_map, device_type=device_type
        )
        with open(Path(base_directory) / "main.cpp", "w") as file:
            file.write(main_file_str)