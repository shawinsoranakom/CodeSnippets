def inner_check_out_mem_format(output):
                d = output.dim()
                if (d == 4 and ((input_mem_format == torch.channels_last)
                                or (module_mem_format == torch.channels_last and module_memformat_affects_out))):
                    self.assertTrue(output.numel() == 0 or output.is_contiguous(memory_format=torch.channels_last))
                elif (d == 5 and ((input_mem_format == torch.channels_last_3d)
                                  or (module_mem_format == torch.channels_last_3d and module_memformat_affects_out))):
                    self.assertTrue(output.numel() == 0 or output.is_contiguous(memory_format=torch.channels_last_3d))
                else:
                    self.assertTrue(output.is_contiguous())