def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        sys.exit(f"{out} already exists; aborting to avoid overwriting")

    gha_expressions_found = False

    for p in Path(".github/workflows").iterdir():
        with open(p, "rb") as f:
            workflow = yaml.safe_load(f)

        for job_name, job in workflow["jobs"].items():
            job_dir = out / p / job_name
            if "steps" not in job:
                continue
            steps = job["steps"]
            index_chars = len(str(len(steps) - 1))
            for i, step in enumerate(steps, start=1):
                extracted = extract(step)
                if extracted:
                    script = extracted["script"]
                    step_name = step.get("name", "")
                    if "${{" in script:
                        gha_expressions_found = True
                        print(
                            f"{p} job `{job_name}` step {i}: {step_name}",
                            file=sys.stderr,
                        )

                    job_dir.mkdir(parents=True, exist_ok=True)

                    sanitized = re.sub(
                        "[^a-zA-Z_]+",
                        "_",
                        f"_{step_name}",
                    ).rstrip("_")
                    extension = extracted["extension"]
                    filename = f"{i:0{index_chars}}{sanitized}{extension}"
                    (job_dir / filename).write_text(script)

    if gha_expressions_found:
        sys.exit(
            "Each of the above scripts contains a GitHub Actions "
            "${{ <expression> }} which must be replaced with an `env` variable"
            " for security reasons."
        )