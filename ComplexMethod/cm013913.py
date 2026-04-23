def generate_svg(
        self, profile_file: str, svg_file: str | None = None
    ) -> str | None:
        """Generate an SVG call graph from a profile file using gprof2dot and graphviz.

        Args:
            profile_file: Path to the pstats profile file.
            svg_file: Optional path for the output SVG. If not provided, uses
                profile_file with .svg extension.

        Returns:
            Path to the generated SVG file, or None if generation failed.
        """
        import os
        import shutil
        import subprocess

        if not shutil.which("gprof2dot"):
            print("gprof2dot not found. Install with: pip install gprof2dot")
            return None

        if not shutil.which("dot"):
            print("graphviz 'dot' not found. Install graphviz package.")
            return None

        if svg_file is None:
            svg_file = profile_file.rsplit(".", 1)[0] + ".svg"

        try:
            # gprof2dot -f pstats profile.prof | dot -Tsvg -o profile.svg
            gprof2dot = subprocess.Popen(
                [
                    "gprof2dot",
                    "-f",
                    "pstats",
                    "--node-label=total-time-percentage",
                    "--node-label=self-time-percentage",
                    "--node-label=total-time",
                    profile_file,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            dot = subprocess.Popen(
                ["dot", "-Tsvg", "-o", svg_file],
                stdin=gprof2dot.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            gprof2dot.stdout.close()  # type: ignore[union-attr]
            _, dot_err = dot.communicate()
            _, gprof2dot_err = gprof2dot.communicate()

            if gprof2dot.returncode != 0:
                print(f"gprof2dot failed: {gprof2dot_err.decode()}")
                return None

            if dot.returncode != 0:
                print(f"graphviz dot failed: {dot_err.decode()}")
                return None

            if not os.path.isfile(svg_file):
                print(f"SVG file was not created: {svg_file}")
                return None

            print(f"SVG call graph saved to: {svg_file}")
            return svg_file

        except Exception as e:
            print(f"Failed to generate SVG: {e}")
            return None