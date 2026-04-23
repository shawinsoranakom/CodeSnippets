def _get_statistics(statistics = None, force_download = True):
    # We log some basic stats about which environment is being used.
    # We simply download a README.md file from HF - all data is made public.
    # This is simply so we can check if some envs are broken or not.
    # You can disable this by commenting the below out
    n_cpus = psutil.cpu_count(logical = False)
    keynames = "\n" + "\n".join(os.environ.keys())
    # Check modelscope for down detection
    global USE_MODELSCOPE
    USE_MODELSCOPE = os.environ.get("UNSLOTH_USE_MODELSCOPE", "0") == "1"

    if statistics is None:
        # Prefer filesystem markers (harder to misidentify) before env-key matching
        try:
            from pathlib import Path

            if Path("/kaggle/working").exists():
                statistics = "kaggle"
            elif Path("/content").exists() and Path("/opt/colab").exists():
                statistics = "colab" if n_cpus == 1 else "colabpro"
            elif Path("/runpod-volume").exists():
                statistics = "runpod"
        except Exception:
            pass

        # Fallback to env-key detection
        if statistics is None:
            if "\nKAGGLE_" in keynames:
                statistics = "kaggle"
            elif "\nCOLAB_" in keynames and n_cpus == 1:
                statistics = "colab"
            elif "\nCOLAB_" in keynames:
                statistics = "colabpro"
            elif "\nRUNPOD_" in keynames:
                statistics = "runpod"
            elif "\nAWS_" in keynames:
                statistics = "aws"
            elif "\nAZURE_" in keynames:
                statistics = "azure"
            # elif "\nK_" in keynames or "\nFUNCTION_" in keynames: statistics = "gcp"
            elif "\nINVOCATION_ID" in keynames:
                statistics = "lambda"
            # else: statistics = "other"
            else:

                def try_vllm_check():
                    vendor_files = (
                        "/sys/class/dmi/id/product_version",
                        "/sys/class/dmi/id/bios_vendor",
                        "/sys/class/dmi/id/product_name",
                        "/sys/class/dmi/id/chassis_asset_tag",
                        "/sys/class/dmi/id/sys_vendor",
                    )

                    for vendor_file in vendor_files:
                        path = Path(vendor_file)
                        if path.is_file():
                            file_content = path.read_text().lower()
                            if "amazon" in file_content:
                                return "aws"
                            elif "microsoft corporation" in file_content:
                                return "azure"
                            elif "google" in file_content:
                                return "gcp"
                    return "other"

                try:
                    statistics = try_vllm_check()
                except Exception:
                    statistics = "other"

    if statistics is not None:
        import tempfile
        from huggingface_hub import snapshot_download
        from unsloth_zoo.rl_environments import execute_with_time_limit

        if has_internet():

            def stats_check():
                with tempfile.TemporaryDirectory(ignore_cleanup_errors = True) as f:
                    snapshot_download(
                        f"unslothai/{statistics}",
                        force_download = True,
                        cache_dir = f,
                        local_dir = f,
                    )

            time_limited_stats_check = execute_with_time_limit(120)(stats_check)
            try:
                time_limited_stats_check()
            except TimeoutError:
                raise TimeoutError(
                    "Unsloth: HuggingFace seems to be down after trying for 120 seconds :(\n"
                    "Check https://status.huggingface.co/ for more details.\n"
                    "As a temporary measure, use modelscope with the same model name ie:\n"
                    "```\n"
                    "pip install modelscope\n"
                    "import os; os.environ['UNSLOTH_USE_MODELSCOPE'] = '1'\n"
                    "from unsloth import FastLanguageModel\n"
                    "model = FastLanguageModel.from_pretrained('unsloth/gpt-oss-20b')\n"
                    "```"
                )
            except Exception:
                logger.debug("Unsloth: stats_check failed with an exception.")