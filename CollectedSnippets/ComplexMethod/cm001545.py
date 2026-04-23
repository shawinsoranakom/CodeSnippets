def prepare_environment():
    torch_index_url = os.environ.get('TORCH_INDEX_URL', "https://download.pytorch.org/whl/cu121")
    torch_command = os.environ.get('TORCH_COMMAND', f"pip install torch==2.1.2 torchvision==0.16.2 --extra-index-url {torch_index_url}")
    if args.use_ipex:
        if platform.system() == "Windows":
            # The "Nuullll/intel-extension-for-pytorch" wheels were built from IPEX source for Intel Arc GPU: https://github.com/intel/intel-extension-for-pytorch/tree/xpu-main
            # This is NOT an Intel official release so please use it at your own risk!!
            # See https://github.com/Nuullll/intel-extension-for-pytorch/releases/tag/v2.0.110%2Bxpu-master%2Bdll-bundle for details.
            #
            # Strengths (over official IPEX 2.0.110 windows release):
            #   - AOT build (for Arc GPU only) to eliminate JIT compilation overhead: https://github.com/intel/intel-extension-for-pytorch/issues/399
            #   - Bundles minimal oneAPI 2023.2 dependencies into the python wheels, so users don't need to install oneAPI for the whole system.
            #   - Provides a compatible torchvision wheel: https://github.com/intel/intel-extension-for-pytorch/issues/465
            # Limitation:
            #   - Only works for python 3.10
            url_prefix = "https://github.com/Nuullll/intel-extension-for-pytorch/releases/download/v2.0.110%2Bxpu-master%2Bdll-bundle"
            torch_command = os.environ.get('TORCH_COMMAND', f"pip install {url_prefix}/torch-2.0.0a0+gite9ebda2-cp310-cp310-win_amd64.whl {url_prefix}/torchvision-0.15.2a0+fa99a53-cp310-cp310-win_amd64.whl {url_prefix}/intel_extension_for_pytorch-2.0.110+gitc6ea20b-cp310-cp310-win_amd64.whl")
        else:
            # Using official IPEX release for linux since it's already an AOT build.
            # However, users still have to install oneAPI toolkit and activate oneAPI environment manually.
            # See https://intel.github.io/intel-extension-for-pytorch/index.html#installation for details.
            torch_index_url = os.environ.get('TORCH_INDEX_URL', "https://pytorch-extension.intel.com/release-whl/stable/xpu/us/")
            torch_command = os.environ.get('TORCH_COMMAND', f"pip install torch==2.0.0a0 intel-extension-for-pytorch==2.0.110+gitba7f6c1 --extra-index-url {torch_index_url}")
    requirements_file = os.environ.get('REQS_FILE', "requirements_versions.txt")
    requirements_file_for_npu = os.environ.get('REQS_FILE_FOR_NPU', "requirements_npu.txt")

    xformers_package = os.environ.get('XFORMERS_PACKAGE', 'xformers==0.0.23.post1')
    clip_package = os.environ.get('CLIP_PACKAGE', "https://github.com/openai/CLIP/archive/d50d76daa670286dd6cacf3bcd80b5e4823fc8e1.zip")
    openclip_package = os.environ.get('OPENCLIP_PACKAGE', "https://github.com/mlfoundations/open_clip/archive/bb6e834e9c70d9c27d0dc3ecedeebeaeb1ffad6b.zip")

    assets_repo = os.environ.get('ASSETS_REPO', "https://github.com/AUTOMATIC1111/stable-diffusion-webui-assets.git")
    stable_diffusion_repo = os.environ.get('STABLE_DIFFUSION_REPO', "https://github.com/Stability-AI/stablediffusion.git")
    stable_diffusion_xl_repo = os.environ.get('STABLE_DIFFUSION_XL_REPO', "https://github.com/Stability-AI/generative-models.git")
    k_diffusion_repo = os.environ.get('K_DIFFUSION_REPO', 'https://github.com/crowsonkb/k-diffusion.git')
    blip_repo = os.environ.get('BLIP_REPO', 'https://github.com/salesforce/BLIP.git')

    assets_commit_hash = os.environ.get('ASSETS_COMMIT_HASH', "6f7db241d2f8ba7457bac5ca9753331f0c266917")
    stable_diffusion_commit_hash = os.environ.get('STABLE_DIFFUSION_COMMIT_HASH', "cf1d67a6fd5ea1aa600c4df58e5b47da45f6bdbf")
    stable_diffusion_xl_commit_hash = os.environ.get('STABLE_DIFFUSION_XL_COMMIT_HASH', "45c443b316737a4ab6e40413d7794a7f5657c19f")
    k_diffusion_commit_hash = os.environ.get('K_DIFFUSION_COMMIT_HASH', "ab527a9a6d347f364e3d185ba6d714e22d80cb3c")
    blip_commit_hash = os.environ.get('BLIP_COMMIT_HASH', "48211a1594f1321b00f14c9f7a5b4813144b2fb9")

    try:
        # the existence of this file is a signal to webui.sh/bat that webui needs to be restarted when it stops execution
        os.remove(os.path.join(script_path, "tmp", "restart"))
        os.environ.setdefault('SD_WEBUI_RESTARTING', '1')
    except OSError:
        pass

    if not args.skip_python_version_check:
        check_python_version()

    startup_timer.record("checks")

    commit = commit_hash()
    tag = git_tag()
    startup_timer.record("git version info")

    print(f"Python {sys.version}")
    print(f"Version: {tag}")
    print(f"Commit hash: {commit}")

    if args.reinstall_torch or not is_installed("torch") or not is_installed("torchvision"):
        run(f'"{python}" -m {torch_command}', "Installing torch and torchvision", "Couldn't install torch", live=True)
        startup_timer.record("install torch")

    if args.use_ipex:
        args.skip_torch_cuda_test = True
    if not args.skip_torch_cuda_test and not check_run_python("import torch; assert torch.cuda.is_available()"):
        raise RuntimeError(
            'Torch is not able to use GPU; '
            'add --skip-torch-cuda-test to COMMANDLINE_ARGS variable to disable this check'
        )
    startup_timer.record("torch GPU test")

    if not is_installed("clip"):
        run_pip(f"install {clip_package}", "clip")
        startup_timer.record("install clip")

    if not is_installed("open_clip"):
        run_pip(f"install {openclip_package}", "open_clip")
        startup_timer.record("install open_clip")

    if (not is_installed("xformers") or args.reinstall_xformers) and args.xformers:
        run_pip(f"install -U -I --no-deps {xformers_package}", "xformers")
        startup_timer.record("install xformers")

    if not is_installed("ngrok") and args.ngrok:
        run_pip("install ngrok", "ngrok")
        startup_timer.record("install ngrok")

    os.makedirs(os.path.join(script_path, dir_repos), exist_ok=True)

    git_clone(assets_repo, repo_dir('stable-diffusion-webui-assets'), "assets", assets_commit_hash)
    git_clone(stable_diffusion_repo, repo_dir('stable-diffusion-stability-ai'), "Stable Diffusion", stable_diffusion_commit_hash)
    git_clone(stable_diffusion_xl_repo, repo_dir('generative-models'), "Stable Diffusion XL", stable_diffusion_xl_commit_hash)
    git_clone(k_diffusion_repo, repo_dir('k-diffusion'), "K-diffusion", k_diffusion_commit_hash)
    git_clone(blip_repo, repo_dir('BLIP'), "BLIP", blip_commit_hash)

    startup_timer.record("clone repositores")

    if not os.path.isfile(requirements_file):
        requirements_file = os.path.join(script_path, requirements_file)

    if not requirements_met(requirements_file):
        run_pip(f"install -r \"{requirements_file}\"", "requirements")
        startup_timer.record("install requirements")

    if not os.path.isfile(requirements_file_for_npu):
        requirements_file_for_npu = os.path.join(script_path, requirements_file_for_npu)

    if "torch_npu" in torch_command and not requirements_met(requirements_file_for_npu):
        run_pip(f"install -r \"{requirements_file_for_npu}\"", "requirements_for_npu")
        startup_timer.record("install requirements_for_npu")

    if not args.skip_install:
        run_extensions_installers(settings_file=args.ui_settings_file)

    if args.update_check:
        version_check(commit)
        startup_timer.record("check version")

    if args.update_all_extensions:
        git_pull_recursive(extensions_dir)
        startup_timer.record("update extensions")

    if "--exit" in sys.argv:
        print("Exiting because of --exit argument")
        exit(0)