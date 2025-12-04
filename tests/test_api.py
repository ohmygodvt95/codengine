"""
Test script for the refactored code execution engine.
"""
import requests
import json

BASE_URL = "http://localhost:8001"


def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")


def test_get_runtimes():
    """Test get runtimes endpoint."""
    print("Testing get runtimes...")
    response = requests.get(f"{BASE_URL}/api/v2/runtimes")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_execute_python():
    """Test Python code execution."""
    print("Testing Python execution...")
    
    payload = {
        "language": "python",
        "version": "3.10",
        "files": [
            {
                "name": "main.py",
                "content": "print('Hello from refactored engine!')\nprint('This is working!')"
            }
        ],
        "stdin": "",
        "args": [],
        "time_limit": 2.0,
        "memory_limit": 256,
        "internet": False
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/execute", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Job ID: {result.get('job_id')}")
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Time: {result.get('time')}s")
    print(f"Stdout: {result.get('stdout')}")
    print(f"Stderr: {result.get('stderr')}")
    print(f"Error: {result.get('error')}\n")


def test_execute_with_stdin():
    """Test execution with stdin."""
    print("Testing execution with stdin...")
    
    payload = {
        "language": "python",
        "version": "3.10",
        "files": [
            {
                "name": "main.py",
                "content": "name = input('Enter your name: ')\nprint(f'Hello, {name}!')"
            }
        ],
        "stdin": "Copilot",
        "args": [],
        "time_limit": 2.0,
        "memory_limit": 256,
        "internet": False
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/execute", json=payload)
    result = response.json()
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Stdout: {result.get('stdout')}")
    print(f"Stderr: {result.get('stderr')}\n")


def test_error_handling():
    """Test error handling."""
    print("Testing error handling - invalid version...")
    
    payload = {
        "language": "python",
        "version": "99.99",
        "files": [
            {
                "name": "main.py",
                "content": "print('This should fail')"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/execute", json=payload)
    result = response.json()
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Error: {result.get('error')}")
    print(f"Stderr: {result.get('stderr')}\n")


def test_timeout():
    """Test timeout handling."""
    print("Testing timeout handling...")
    
    payload = {
        "language": "python",
        "version": "3.10",
        "files": [
            {
                "name": "main.py",
                "content": "import time\ntime.sleep(10)\nprint('Should not reach here')"
            }
        ],
        "time_limit": 1.0
    }
    
    response = requests.post(f"{BASE_URL}/api/v2/execute", json=payload)
    result = response.json()
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Stderr: {result.get('stderr')}")
    print(f"Time: {result.get('time')}s\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Code Execution Engine - Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_health_check()
        test_get_runtimes()
        test_execute_python()
        test_execute_with_stdin()
        test_error_handling()
        test_timeout()
        
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server.")
        print("Make sure the server is running: uvicorn main:app --reload")
    except Exception as e:
        print(f"ERROR: {str(e)}")
