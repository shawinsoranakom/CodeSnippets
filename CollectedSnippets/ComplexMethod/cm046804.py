def test_windows_cuda_prefers_published_asset_from_selected_release(
        self, monkeypatch
    ):
        host = make_host(system = "Windows", machine = "AMD64")
        host.driver_cuda_version = (12, 4)
        mock_windows_runtime(monkeypatch, ["cuda12"])
        asset_name = "llama-b9000-bin-win-cuda-12.4-x64.zip"
        release = make_release(
            [
                make_artifact(
                    asset_name,
                    install_kind = "windows-cuda",
                    runtime_line = "cuda12",
                    coverage_class = None,
                    supported_sms = [],
                    min_sm = None,
                    max_sm = None,
                    bundle_profile = None,
                )
            ],
            release_tag = "llama-prebuilt-latest",
            upstream_tag = "b9000",
            assets = {asset_name: f"https://published.example/{asset_name}"},
        )
        checksums = make_checksums_with_source(
            [asset_name],
            release_tag = release.release_tag,
            upstream_tag = "b9000",
        )

        monkeypatch.setattr(
            INSTALL_LLAMA_PREBUILT,
            "iter_resolved_published_releases",
            lambda requested_tag, published_repo, published_release_tag = "": iter(
                [
                    INSTALL_LLAMA_PREBUILT.ResolvedPublishedRelease(
                        bundle = release,
                        checksums = checksums,
                    )
                ]
            ),
        )
        monkeypatch.setattr(
            INSTALL_LLAMA_PREBUILT,
            "github_release_assets",
            lambda repo, tag: (_ for _ in ()).throw(
                AssertionError(
                    "published Windows CUDA choice should not query upstream"
                )
            ),
        )

        requested_tag, resolved_tag, attempts, approved = resolve_install_attempts(
            "latest",
            host,
            "unslothai/llama.cpp",
            "",
        )

        assert requested_tag == "latest"
        assert resolved_tag == "b9000"
        assert attempts[0].name == asset_name
        assert attempts[0].source_label == "published"
        assert attempts[0].expected_sha256 == "a" * 64
        assert approved.release_tag == "llama-prebuilt-latest"