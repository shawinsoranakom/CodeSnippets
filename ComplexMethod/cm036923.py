async def test_environment_variable_script_loading(self):
        """Test that environment variables correctly specify script location
        and loading."""
        try:
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Customer writes a script in a specific directory
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from fastapi import Request

async def custom_sagemaker_ping_handler():
    return {
        "status": "healthy",
        "source": "env_loaded_script",
        "method": "environment_variable_loading"
    }

async def custom_sagemaker_invocation_handler(request: Request):
    return {
        "predictions": ["Loaded via environment variables"],
        "source": "env_loaded_script",
        "method": "environment_variable_loading"
    }
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Test environment variable script loading
            env_vars = {
                SageMakerEnvVars.SAGEMAKER_MODEL_PATH: script_dir,
                SageMakerEnvVars.CUSTOM_SCRIPT_FILENAME: script_name,
            }

            args = [
                "--dtype",
                "bfloat16",
                "--max-model-len",
                "2048",
                "--enforce-eager",
                "--max-num-seqs",
                "32",
            ]

            with RemoteOpenAIServer(
                MODEL_NAME_SMOLLM, args, env_dict=env_vars
            ) as server:
                ping_response = requests.get(server.url_for("ping"))
                assert ping_response.status_code == 200
                ping_data = ping_response.json()

                invoke_response = requests.post(
                    server.url_for("invocations"),
                    json={
                        "model": MODEL_NAME_SMOLLM,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 5,
                    },
                )
                assert invoke_response.status_code == 200
                invoke_data = invoke_response.json()

                # Verify that the script was loaded via environment variables
                assert ping_data["source"] == "env_loaded_script"
                assert ping_data["method"] == "environment_variable_loading"
                assert invoke_data["source"] == "env_loaded_script"
                assert invoke_data["method"] == "environment_variable_loading"

        finally:
            os.unlink(script_path)