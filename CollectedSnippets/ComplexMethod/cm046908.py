def cleanup(self):
        if not hasattr(self, "vllm_process"):
            return

        vllm_process = self.vllm_process
        print("Attempting to terminate the VLLM server gracefully...")
        try:
            vllm_process.terminate()
            vllm_process.wait(timeout = 10)
            print("Server terminated gracefully.")
        except subprocess.TimeoutExpired:
            print(
                "Server did not terminate gracefully after 10 seconds. Forcing kill..."
            )
            vllm_process.kill()
            vllm_process.wait()
            print("Server killed forcefully.")
        except Exception as e:
            print(f"An error occurred while trying to stop the process: {e}")
            try:
                if vllm_process.poll() is None:
                    print("Attempting forceful kill due to error...")
                    vllm_process.kill()
                    vllm_process.wait()
                    print("Server killed forcefully after error.")
            except Exception as kill_e:
                print(f"Error during forceful kill: {kill_e}")
        for _ in range(10):
            torch.cuda.empty_cache()
            gc.collect()

        # Delete vLLM module as well
        if hasattr(self, "_delete_vllm"):
            self._delete_vllm(llm = None)