def test_auto_simd(self):
        vec_amx = cpu_vec_isa.supported_vec_isa_list[0]
        vec_avx512_vnni = cpu_vec_isa.supported_vec_isa_list[1]
        vec_avx512 = cpu_vec_isa.supported_vec_isa_list[2]
        vec_avx2 = cpu_vec_isa.supported_vec_isa_list[3]
        self.assertTrue(vec_amx.bit_width() == 512)
        self.assertTrue(vec_amx.nelements() == 16)
        self.assertTrue(vec_amx.nelements(torch.bfloat16) == 32)
        self.assertTrue(vec_avx512_vnni.bit_width() == 512)
        self.assertTrue(vec_avx512_vnni.nelements(torch.int8) == 64)
        self.assertTrue(vec_avx512_vnni.nelements(torch.uint8) == 64)
        self.assertTrue(vec_avx512.bit_width() == 512)
        self.assertTrue(vec_avx2.bit_width() == 256)
        self.assertTrue(vec_avx512.nelements() == 16)
        self.assertTrue(vec_avx2.nelements() == 8)
        self.assertTrue(vec_avx512.nelements(torch.bfloat16) == 32)
        self.assertTrue(vec_avx2.nelements(torch.bfloat16) == 16)

        with config.patch({"cpp.simdlen": 0}):
            isa = cpu_vec_isa.pick_vec_isa()
            self.assertFalse(isa)

        with config.patch({"cpp.simdlen": 1}):
            isa = cpu_vec_isa.pick_vec_isa()
            self.assertFalse(isa)

        with config.patch({"cpp.simdlen": 257}):
            isa = cpu_vec_isa.pick_vec_isa()
            self.assertFalse(isa)

        with config.patch({"cpp.simdlen": 513}):
            isa_list = cpu_vec_isa.valid_vec_isa_list()
            if vec_avx512 in isa_list:
                self.assertFalse(isa)

        with config.patch({"cpp.simdlen": 512}):
            isa_list = cpu_vec_isa.valid_vec_isa_list()
            isa = cpu_vec_isa.pick_vec_isa()
            if vec_amx in isa_list:
                self.assertTrue(isa == vec_amx)
            elif vec_avx512_vnni in isa_list:
                self.assertTrue(isa == vec_avx512_vnni)
            elif vec_avx512 in isa_list:
                self.assertTrue(isa == vec_avx512)

        with config.patch({"cpp.simdlen": 256}):
            isa_list = cpu_vec_isa.valid_vec_isa_list()
            if vec_avx2 in isa_list:
                isa = cpu_vec_isa.pick_vec_isa()
                self.assertTrue(isa == vec_avx2)

        pre_var = os.getenv("ATEN_CPU_CAPABILITY")
        if pre_var:
            os.environ.pop("ATEN_CPU_CAPABILITY")

        try:
            with config.patch({"cpp.simdlen": None}):
                isa = cpu_vec_isa.pick_vec_isa()
                if vec_amx in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_amx)
                elif vec_avx512_vnni in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512_vnni)
                elif vec_avx512 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512)
                else:
                    self.assertTrue(isa == vec_avx2)

            with config.patch({"cpp.simdlen": None}):
                os.environ["ATEN_CPU_CAPABILITY"] = "avx2"
                isa = cpu_vec_isa.pick_vec_isa()
                if vec_amx in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx2)
                if vec_avx512_vnni in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx2)
                elif vec_avx512 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx2)
                elif vec_avx2 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx2)

            with config.patch({"cpp.simdlen": None}):
                os.environ["ATEN_CPU_CAPABILITY"] = "avx512"
                isa = cpu_vec_isa.pick_vec_isa()
                if vec_amx in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_amx)
                elif vec_avx512_vnni in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512_vnni)
                elif vec_avx512 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512)
                else:
                    self.assertTrue(isa == vec_avx2)

            with config.patch({"cpp.simdlen": None}):
                os.environ["ATEN_CPU_CAPABILITY"] = "default"
                isa = cpu_vec_isa.pick_vec_isa()
                self.assertFalse(isa)

            with config.patch({"cpp.simdlen": None}):
                os.environ["ATEN_CPU_CAPABILITY"] = "zvector"
                isa = cpu_vec_isa.pick_vec_isa()
                if vec_amx in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_amx)
                elif vec_avx512_vnni in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512_vnni)
                elif vec_avx512 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512)
                else:
                    self.assertTrue(isa == vec_avx2)

            with config.patch({"cpp.simdlen": None}):
                os.environ["ATEN_CPU_CAPABILITY"] = "vsx"
                isa = cpu_vec_isa.pick_vec_isa()
                if vec_amx in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_amx)
                elif vec_avx512_vnni in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512_vnni)
                elif vec_avx512 in cpu_vec_isa.valid_vec_isa_list():
                    self.assertTrue(isa == vec_avx512)
                else:
                    self.assertTrue(isa == vec_avx2)

        finally:
            if pre_var:
                os.environ["ATEN_CPU_CAPABILITY"] = pre_var
            elif os.getenv("ATEN_CPU_CAPABILITY"):
                os.environ.pop("ATEN_CPU_CAPABILITY")