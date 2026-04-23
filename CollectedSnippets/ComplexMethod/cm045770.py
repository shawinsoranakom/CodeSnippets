def run_test(
    *,
    tmp_path: pathlib.Path,
    port: int,
    rate: int,
    processes: int,
    expected_upscaling: bool = False,
    expected_downscaling: bool = False,
    expected_stable: bool = False,
):
    pstorage = str(tmp_path / "PStorage")
    program_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "example_scaling.py"
    )
    env_base = os.environ.copy()

    process_handles = create_process_handles(
        processes=processes,
        threads=1,
        first_port=port,
        run_id=str(uuid.uuid4()),
        env_base=env_base,
        program="python",
        arguments=[
            program_path,
            "--rate",
            str(rate),
            "--persistent-storage-path",
            pstorage,
        ],
    )

    state = wait_for_scaling_event(process_handles)

    assert state.needs_downscaling == expected_downscaling
    assert state.needs_upscaling == expected_upscaling
    if expected_stable:
        assert not state.needs_downscaling
        assert not state.needs_upscaling
        assert not state.has_process_with_error
        assert state.has_working_process