"""
Port Management Module

This module provides utilities for managing port availability, checking for
port conflicts, and handling process cleanup for network services.
"""

import socket
import subprocess
import time
import logging
import platform
import signal
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is currently in use.

    Args:
        port: Port number to check
        host: Host address to check (default: 127.0.0.1)

    Returns:
        True if port is in use, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.error(f"Error checking port {port}: {e}")
        return False


def get_process_using_port(port: int) -> Optional[int]:
    """
    Get the PID of the process using a specific port.

    Args:
        port: Port number to check

    Returns:
        PID of the process using the port, or None if not found
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            # Use lsof on macOS
            cmd = ["lsof", "-ti", f":{port}"]
        elif system == "Linux":
            # Use ss on Linux (more reliable than lsof)
            cmd = ["ss", "-lptn", f"sport = :{port}"]
        else:
            logger.warning(f"Unsupported platform: {system}")
            return None

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            if system == "Darwin":
                # lsof returns PID directly
                pids = result.stdout.strip().split('\n')
                if pids:
                    return int(pids[0])
            elif system == "Linux":
                # Parse ss output to extract PID
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f":{port}" in line and "pid=" in line:
                        # Extract PID from format: users:(("process",pid=12345,fd=3))
                        pid_part = line.split("pid=")[1]
                        pid = pid_part.split(",")[0].split(")")[0]
                        return int(pid)

        return None

    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Error getting process for port {port}: {e}")
        return None


def kill_process_on_port(port: int, force: bool = False, max_retries: int = 3) -> bool:
    """
    Kill the process using a specific port with retry logic.

    Args:
        port: Port number to free
        force: Use SIGKILL instead of SIGTERM if True
        max_retries: Maximum number of attempts to kill the process

    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        pid = get_process_using_port(port)

        if pid is None:
            logger.info(f"No process found using port {port}")
            return True

        try:
            signal_type = signal.SIGKILL if force or attempt > 0 else signal.SIGTERM
            logger.info(f"Attempting to kill process {pid} on port {port} (attempt {attempt + 1}/{max_retries})")

            import os
            os.kill(pid, signal_type)

            # Wait briefly for process to terminate
            time.sleep(0.5)

            # Check if port is now free
            if not is_port_in_use(port):
                logger.info(f"Successfully freed port {port}")
                return True

        except ProcessLookupError:
            logger.info(f"Process {pid} already terminated")
            return True
        except PermissionError:
            logger.error(f"Permission denied to kill process {pid}")
            return False
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")

    logger.error(f"Failed to free port {port} after {max_retries} attempts")
    return False


def find_available_port(start_port: int = 8000, end_port: int = 9000, host: str = "127.0.0.1") -> Optional[int]:
    """
    Find an available port in the specified range.

    Args:
        start_port: Starting port number (inclusive)
        end_port: Ending port number (exclusive)
        host: Host address to check

    Returns:
        Available port number, or None if no ports available
    """
    for port in range(start_port, end_port):
        if not is_port_in_use(port, host):
            # Double-check by trying to bind to the port
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind((host, port))
                    logger.info(f"Found available port: {port}")
                    return port
            except OSError:
                continue

    logger.error(f"No available ports found in range {start_port}-{end_port}")
    return None


def wait_for_port(port: int, timeout: int = 10, check_interval: float = 0.5, host: str = "127.0.0.1") -> bool:
    """
    Wait for a port to become available (for service startup).

    Args:
        port: Port number to wait for
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        host: Host address to check

    Returns:
        True if port becomes available, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            logger.info(f"Port {port} is now available")
            return True
        time.sleep(check_interval)

    logger.warning(f"Timeout waiting for port {port} to become available")
    return False


def cleanup_zombie_processes(service_name: str = "webhook") -> int:
    """
    Find and cleanup zombie/orphaned processes by service name.

    Args:
        service_name: Name pattern to search for in process list

    Returns:
        Number of processes cleaned up
    """
    system = platform.system()
    cleaned = 0

    try:
        if system in ["Darwin", "Linux"]:
            # Use ps to find processes matching the service name
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if service_name in line and "python" in line:
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                import os
                                os.kill(pid, signal.SIGTERM)
                                cleaned += 1
                                logger.info(f"Cleaned up process {pid}: {line[:100]}")
                            except (ValueError, ProcessLookupError, PermissionError) as e:
                                logger.debug(f"Could not clean up process: {e}")

    except Exception as e:
        logger.error(f"Error cleaning up zombie processes: {e}")

    return cleaned


def get_port_info(port: int) -> dict:
    """
    Get detailed information about a port and any process using it.

    Args:
        port: Port number to inspect

    Returns:
        Dictionary with port information
    """
    info = {
        "port": port,
        "in_use": is_port_in_use(port),
        "pid": None,
        "process_name": None,
        "command": None
    }

    if info["in_use"]:
        pid = get_process_using_port(port)
        info["pid"] = pid

        if pid:
            try:
                # Get process details
                result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    info["process_name"] = result.stdout.strip()

                # Get full command
                result = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    info["command"] = result.stdout.strip()
            except Exception as e:
                logger.debug(f"Could not get process details: {e}")

    return info