def main():
    subdirectory, subprocess_args = parse_args()

    fixed_args = [fix_arg(subdirectory, arg) for arg in subprocess_args]
    try:
        subprocess.run(fixed_args, cwd=subdirectory, check=True)
    except subprocess.CalledProcessError as ex:
        sys.exit(ex.returncode)