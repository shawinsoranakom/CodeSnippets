def ensure_multipart_is_installed() -> None:
    try:
        from python_multipart import __version__

        # Import an attribute that can be mocked/deleted in testing
        assert __version__ > "0.0.12"
    except (ImportError, AssertionError):
        try:
            # __version__ is available in both multiparts, and can be mocked
            from multipart import (  # type: ignore[no-redef,import-untyped]  # ty: ignore[unused-ignore-comment]
                __version__,
            )

            assert __version__
            try:
                # parse_options_header is only available in the right multipart
                from multipart.multipart import (  # type: ignore[import-untyped]  # ty: ignore[unused-ignore-comment]
                    parse_options_header,
                )

                assert parse_options_header
            except ImportError:
                logger.error(multipart_incorrect_install_error)
                raise RuntimeError(multipart_incorrect_install_error) from None
        except ImportError:
            logger.error(multipart_not_installed_error)
            raise RuntimeError(multipart_not_installed_error) from None