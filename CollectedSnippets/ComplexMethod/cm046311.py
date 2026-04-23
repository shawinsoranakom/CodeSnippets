def export_imx(self, prefix=colorstr("IMX:")):
        """Export YOLO model to IMX format."""
        assert LINUX, (
            "Export only supported on Linux."
            "See https://developer.aitrios.sony-semicon.com/en/docs/raspberry-pi-ai-camera/imx500-converter?version=3.17.3&progLang="
        )
        assert IS_PYTHON_MINIMUM_3_9, "IMX export is only supported on Python 3.9 or above."

        if getattr(self.model, "end2end", False):
            raise ValueError("IMX export is not supported for end2end models.")
        check_requirements(
            (
                "model-compression-toolkit>=2.4.1",
                "edge-mdt-cl<1.1.0",
                "edge-mdt-tpc>=1.2.0",
                "pydantic<=2.11.7",
            )
        )

        check_requirements("imx500-converter[pt]>=3.17.3")
        from ultralytics.utils.export.imx import torch2imx

        # Install Java>=17
        try:
            java_output = subprocess.run(["java", "--version"], check=True, capture_output=True).stdout.decode()
            version_match = re.search(r"(?:openjdk|java) (\d+)", java_output)
            java_version = int(version_match.group(1)) if version_match else 0
            assert java_version >= 17, "Java version too old"
        except (FileNotFoundError, subprocess.CalledProcessError, AssertionError):
            if IS_UBUNTU or IS_DEBIAN_TRIXIE:
                LOGGER.info(f"\n{prefix} installing Java 21 for Ubuntu...")
                check_apt_requirements(["openjdk-21-jre"])
            elif IS_RASPBERRYPI or IS_DEBIAN_BOOKWORM:
                LOGGER.info(f"\n{prefix} installing Java 17 for Raspberry Pi or Debian ...")
                check_apt_requirements(["openjdk-17-jre"])

        return torch2imx(
            model=self.model,
            output_dir=str(self.file).replace(self.file.suffix, "_imx_model/"),
            conf=self.args.conf,
            iou=self.args.iou,
            max_det=self.args.max_det,
            metadata=self.metadata,
            dataset=self.get_int8_calibration_dataloader(prefix),
            prefix=prefix,
        )