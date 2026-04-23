def _execute_doc2md(args):
        if args.formats:
            from ._doc2md import supported_formats

            fmts = supported_formats()
            print("Supported formats: " + ", ".join(f".{f}" for f in fmts))
            return

        if not args.input:
            logger.error("--input is required when --formats is not set")
            sys.exit(2)

        from ._doc2md import convert
        from pathlib import Path

        output = args.output
        quiet = args.quiet

        # Build converter kwargs from CLI args
        converter_kwargs = {}
        if args.no_drawings:
            converter_kwargs["extract_drawings"] = False
        if args.no_headers_footers:
            converter_kwargs["extract_headers_footers"] = False
        if args.sheet_name is not None:
            converter_kwargs["sheet_name"] = args.sheet_name
        if args.max_rows is not None:
            converter_kwargs["max_rows"] = args.max_rows

        t1 = time.time()
        try:
            result = convert(args.input, output=output, **converter_kwargs)
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            sys.exit(1)

        elapsed = (time.time() - t1) * 1000
        if not quiet:
            logger.info(f"Conversion done in {elapsed:.0f} ms")

        if output:
            if not quiet:
                logger.info(f"Saved to: {output}")
                if result.images:
                    logger.info(f"Images saved to: {Path(output).parent / 'images'}/")
        else:
            print(result.markdown)