def __init__(self, test_input=""):
        self.cpuinfo = []
        if platform.system() in ["Windows", "Darwin"]:
            raise RuntimeError(f"{platform.system()} is not supported!!!")
        elif platform.system() == "Linux":
            # Sample output of: `lscpu --parse=CPU,Core,Socket,Node`
            #
            # # The following is the parsable format, which can be fed to other
            # # programs. Each different item in every column has an unique ID
            # # starting from zero.
            # # CPU,Core,Socket,Node
            # 0,0,0,0
            # 1,1,0,0
            # ...
            if test_input == "":
                lscpu_cmd = ["lscpu", "--parse=CPU,Core,Socket,Node"]
                lscpu_info = subprocess.check_output(
                    lscpu_cmd, universal_newlines=True
                ).split("\n")
            else:
                lscpu_info = test_input.split("\n")

            # Get information about  cpu, core, socket and node
            for line in lscpu_info:
                pattern = r"^([\d]+,[\d]+,[\d]+,[\d]?)"
                regex_out = re.search(pattern, line)
                if regex_out:
                    self.cpuinfo.append(regex_out.group(1).strip().split(","))

            # physical cores := core column in lscpu output
            #  logical cores :=  cPU column in lscpu output
            self.node_nums = int(max(line[3] for line in self.cpuinfo)) + 1
            self.node_physical_cores: list[list[int]] = []  # node_id is index
            self.node_logical_cores: list[list[int]] = []  # node_id is index
            self.physical_core_node_map = {}  # physical core to numa node id
            self.logical_core_node_map = {}  # logical core to numa node id

            for node_id in range(self.node_nums):
                cur_node_physical_core = []
                cur_node_logical_core = []
                for cpuinfo in self.cpuinfo:
                    nid = cpuinfo[3] if cpuinfo[3] != "" else "0"
                    if node_id == int(nid):
                        if int(cpuinfo[1]) not in cur_node_physical_core:
                            cur_node_physical_core.append(int(cpuinfo[1]))
                            self.physical_core_node_map[int(cpuinfo[1])] = int(node_id)
                        cur_node_logical_core.append(int(cpuinfo[0]))
                        self.logical_core_node_map[int(cpuinfo[0])] = int(node_id)
                self.node_physical_cores.append(cur_node_physical_core)
                self.node_logical_cores.append(cur_node_logical_core)