def process_file(
    input_filename: str, output_filename: str, auto_generate_params: bool = True
) -> str:
    with open(input_filename) as file:
        source_code = file.read()

    transformed_code = source_code
    if "def triton_(" in source_code:
        raise RuntimeError(
            "Need to run original Pytorch code generating kernels with TORCHINDUCTOR_UNIQUE_KERNEL_NAMES=1"
        )
    # transformed_code = rename_kernels(transformed_code)
    transformed_code = remove_triton_function_declaration(transformed_code)
    transformed_code = remove_async_compile(transformed_code)

    launch_params_filename = f"{input_filename}.launch_params"

    # Auto-generate launch_params if they don't exist and auto_generate_params is True
    if not os.path.exists(launch_params_filename) and auto_generate_params:
        print(f"Launch params file {launch_params_filename} not found. Generating...")
        try:
            # Set environment variable and run the input file
            env = os.environ.copy()
            env["TORCHINDUCTOR_DUMP_LAUNCH_PARAMS"] = "1"

            result = subprocess.run(
                [sys.executable, input_filename],
                env=env,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(input_filename) or ".",
            )

            if result.returncode != 0:
                print(f"Error running {input_filename}:")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                raise RuntimeError(
                    f"Failed to generate launch params. Command failed with return code {result.returncode}"
                )

            print(f"Successfully generated {launch_params_filename}")

        except Exception as e:
            raise RuntimeError(
                f"Failed to generate launch params by running {input_filename}: {str(e)}"
            ) from e

    if not os.path.exists(launch_params_filename):
        raise RuntimeError(
            f"Missing {launch_params_filename}. Run `TORCHINDUCTOR_DUMP_LAUNCH_PARAMS=1 python {input_filename}` first."
        )

    with open(launch_params_filename) as f:
        launch_params_meta = f.readlines()

    split_params = [i.split("|") for i in launch_params_meta]
    kernel_args_grid = {a.strip(): (b.strip(), c.strip()) for a, b, c in split_params}
    transformed_code = add_launch_params(transformed_code, kernel_args_grid)

    with open(output_filename, "w") as file:
        file.write(transformed_code)
    print(f"Successfully generated {output_filename}")
    return transformed_code