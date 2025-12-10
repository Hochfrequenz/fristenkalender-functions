"""Tests for Docker image build and runtime."""
import subprocess
import time

import pytest
import requests


@pytest.fixture(scope="module")
def docker_container():
    """Build and run the Docker container for testing."""
    image_name = "fristenkalender-functions-test"
    container_name = "fristenkalender-test-container"

    # Build the Docker image
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert build_result.returncode == 0, f"Docker build failed: {build_result.stderr}"

    # Run the container
    run_result = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            "8080:80",
            image_name,
        ],
        capture_output=True,
        text=True,
    )
    assert run_result.returncode == 0, f"Docker run failed: {run_result.stderr}"

    # Wait for container to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    else:
        # Cleanup and fail if container didn't start
        subprocess.run(["docker", "stop", container_name], capture_output=True)
        subprocess.run(["docker", "rm", container_name], capture_output=True)
        pytest.fail("Container failed to start within timeout")

    yield "http://localhost:8080"

    # Cleanup
    subprocess.run(["docker", "stop", container_name], capture_output=True)
    subprocess.run(["docker", "rm", container_name], capture_output=True)


@pytest.mark.docker
class TestDockerImage:
    def test_health_endpoint_is_healthy(self, docker_container):
        """Test that the health endpoint returns healthy status."""
        response = requests.get(f"{docker_container}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_version_endpoint_returns_version_info(self, docker_container):
        """Test that the version endpoint returns version information."""
        response = requests.get(f"{docker_container}/version", timeout=5)
        assert response.status_code == 200
        version_info = response.json()
        assert "commit_hash" in version_info
        assert "build_date" in version_info
        assert "tag" in version_info

    def test_docs_endpoint_available(self, docker_container):
        """Test that the OpenAPI docs are available."""
        response = requests.get(f"{docker_container}/docs", timeout=5)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
