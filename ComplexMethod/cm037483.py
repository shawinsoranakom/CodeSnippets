def get_cpu_architecture(cls) -> CpuArchEnum:
        """
        Determine the CPU architecture of the current system.
        Returns CpuArchEnum indicating the architecture type.
        """
        machine = platform.machine().lower()

        if machine in ("x86_64", "amd64", "i386", "i686"):
            return CpuArchEnum.X86
        elif machine.startswith("arm") or machine.startswith("aarch"):
            return CpuArchEnum.ARM
        elif machine.startswith("ppc"):
            return CpuArchEnum.POWERPC
        elif machine == "s390x":
            return CpuArchEnum.S390X
        elif machine.startswith("riscv"):
            return CpuArchEnum.RISCV

        return CpuArchEnum.OTHER if machine else CpuArchEnum.UNKNOWN