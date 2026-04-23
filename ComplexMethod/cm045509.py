def generate_api_reference() -> None:
    """Generate API documentation before building."""
    reference_dir = Path(__file__).parent / "reference"

    # Only generate if reference directory doesn't exist
    if reference_dir.exists():
        print("📁 Reference directory already exists, skipping API generation")
        return

    script_path = Path(__file__).parent / "generate_api_reference.py"
    if script_path.exists():
        print("🔄 Generating API documentation...")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=script_path.parent,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ API documentation generated successfully")
            # Print the output for visibility
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate API documentation: {e}")
            if e.stdout:
                print(f"stdout: {e.stdout}")
            if e.stderr:
                print(f"stderr: {e.stderr}")
            # Don't fail the build, just warn
    else:
        print(f"⚠️  API documentation generator not found at {script_path}")