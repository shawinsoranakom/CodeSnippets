async def test_customer_script_functions_auto_loaded(self):
        """Test customer scenario: script functions automatically override
        framework defaults."""
        try:
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Customer writes a script file with ping() and invoke() functions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from fastapi import Request

async def custom_sagemaker_ping_handler():
    return {
        "status": "healthy",
        "source": "customer_override", 
        "message": "Custom ping from customer script"
    }

async def custom_sagemaker_invocation_handler(request: Request):
    return {
        "predictions": ["Custom response from customer script"],
        "source": "customer_override"
    }
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

            # Customer sets SageMaker environment variables to point to their script
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
                # Customer tests their server and sees their overrides work
                # automatically
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

                # Customer sees their functions are used
                assert ping_data["source"] == "customer_override"
                assert ping_data["message"] == "Custom ping from customer script"
                assert invoke_data["source"] == "customer_override"
                assert invoke_data["predictions"] == [
                    "Custom response from customer script"
                ]

        finally:
            os.unlink(script_path)