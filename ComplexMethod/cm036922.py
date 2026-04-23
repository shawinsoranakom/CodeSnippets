async def test_handler_priority_order(self):
        """Test priority: @custom_ping_handler/@custom_invocation_handler
        decorators vs script functions."""
        try:
            from model_hosting_container_standards.sagemaker.config import (
                SageMakerEnvVars,
            )
        except ImportError:
            pytest.skip("model-hosting-container-standards not available")

        # Customer writes a script with both decorator and regular functions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import model_hosting_container_standards.sagemaker as sagemaker_standards
from fastapi import Request

# Customer uses @custom_ping_handler decorator (higher priority than script functions)
@sagemaker_standards.custom_ping_handler
async def decorated_ping():
    return {
        "status": "healthy",
        "source": "ping_decorator_in_script", 
        "priority": "decorator"
    }

# Customer also has a regular function (lower priority than
# @custom_ping_handler decorator)
async def custom_sagemaker_ping_handler():
    return {
        "status": "healthy",
        "source": "script_function",
        "priority": "function"
    }

# Customer has a regular invoke function
async def custom_sagemaker_invocation_handler(request: Request):
    return {
        "predictions": ["Script function response"],
        "source": "script_invoke_function",
        "priority": "function"
    }
"""
            )
            script_path = f.name

        try:
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)

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

                # @custom_ping_handler decorator has higher priority than
                # script function
                assert ping_data["source"] == "ping_decorator_in_script"
                assert ping_data["priority"] == "decorator"

                # Script function is used for invoke
                assert invoke_data["source"] == "script_invoke_function"
                assert invoke_data["priority"] == "function"

        finally:
            os.unlink(script_path)