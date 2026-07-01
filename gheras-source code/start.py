"""
Gheras - Project Launcher
Starts backend (Django) and frontend (Vite) concurrently.
Works on Windows. Requires Python 3.10+, Bun, and Docker.
"""
# This script serves as the main entry point for launching the Gheras application. It checks for required dependencies (Python, Bun, Docker), verifies that necessary ports are available, checks database connectivity, and then starts both the backend (Django) and frontend (Vite) servers concurrently. The script also includes utility functions for printing colored messages, checking for running processes on specific ports, and handling user input to terminate conflicting processes if needed. Overall, it provides a convenient way to set up and run the Gheras application with proper checks and feedback for the user.
import os
import sys
import socket
import subprocess
import signal
import time
from pathlib import Path

# Define constants for the project root, backend and frontend directories, database configuration, server ports, and Docker container name. These constants are used throughout the script to manage paths, database connections, and server configurations.
ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

# Database config (must match backend/app.py)
DB_NAME = "qura"
DB_USER = "qura"
DB_PASS = "qura"
DB_HOST = "localhost"
DB_PORT = 5434

# Server ports
BACKEND_PORT = 8001
FRONTEND_PORT = 5173

# Docker container name for the PostgreSQL database. This is used in the check_database function to provide instructions for starting the database container if it is not reachable. The script assumes that the database runs in a Docker container with this name, and it provides commands for running or starting the container as needed.
DOCKER_CONTAINER = "gheras-db"

# Colors class defines ANSI escape codes for colored and formatted terminal output. It includes constants for red, green, yellow, cyan, bold text, and reset to default formatting. This class is used in the cprint function to print messages in different colors for better visibility and user experience when running the launcher script.
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

# Utility function to print messages in a specified color. It takes a color code from the Colors class and a message string, and prints the message with the given color formatting. After printing, it resets the color to default to ensure that subsequent terminal output is not affected by the color formatting.
def cprint(color, msg):
    print(f"{color}{msg}{Colors.RESET}")

# The main function of the script that orchestrates the launching process. It displays a banner, checks for required dependencies (Python, Bun, Docker), verifies that the necessary ports for the backend and frontend servers are available, checks database connectivity, and then starts both servers concurrently using subprocess.Popen. The function also handles user input to keep the script running until the user decides to quit by pressing 'q' or 'Q'.
def banner():
    cprint(Colors.CYAN, """
  ╔══════════════════════════════════════╗
  ║          Gheras Launcher             ║
  ╚══════════════════════════════════════╝
""")

# The main function that orchestrates the launching process. It displays a banner, checks for required dependencies (Python, Bun, Docker), verifies that the necessary ports for the backend and frontend servers are available, checks database connectivity, and then starts both servers concurrently using subprocess.Popen. The function also handles user input to keep the script running until the user decides to quit by pressing 'q' or 'Q'.
def check_command(cmd):
    """Check if a command exists on PATH."""
    try:
        subprocess.run(
            [cmd, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        return False

# This function checks if a specific command (such as Python, Bun, or Docker) is available on the system's PATH by attempting to run the command with a version flag. If the command is found and runs successfully, it returns True; otherwise, it catches the FileNotFoundError and returns False, indicating that the command is not available. This function is used in the main function to verify that all required dependencies are installed before attempting to launch the application.
def get_pid_on_port(port):
    """Return list of PIDs listening on the given port, or empty list."""
    pids = []
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and "LISTENING" in line:
                    pid = int(parts[-1])
                    if pid not in pids:
                        pids.append(pid)
        else:
            # Linux/macOS
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True
            )
            for line in result.stdout.strip().splitlines():
                if line.strip().isdigit():
                    pids.append(int(line.strip()))
    except Exception:
        pass
    return pids


def kill_pids(pids):
    """Kill a list of PIDs."""
    for pid in pids:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.kill(pid, signal.SIGTERM)
            cprint(Colors.YELLOW, f"    Killed PID {pid}")
        except Exception as e:
            cprint(Colors.RED, f"    Failed to kill PID {pid}: {e}")


def check_port(port, name):
    """Check if a port is in use. If so, offer to kill the process."""
    pids = get_pid_on_port(port)
    if not pids:
        return True

    cprint(Colors.YELLOW, f"\n  Hey dude, port {port} ({name}) is already in use!")
    cprint(Colors.YELLOW, f"  PIDs on that port: {pids}")
    answer = input(f"  Want me to terminate them and take over? [y/N] ").strip().lower()
    if answer in ("y", "yes"):
        kill_pids(pids)
        time.sleep(1)
        # Verify it's free now
        if get_pid_on_port(port):
            cprint(Colors.RED, f"  Port {port} still occupied after killing. Aborting.")
            return False
        cprint(Colors.GREEN, f"  Port {port} is now free.")
        return True
    else:
        cprint(Colors.RED, f"  Can't start {name} without port {port}. Aborting.")
        return False


def check_database():
    """Try to connect to the PostgreSQL database and report status."""
    cprint(Colors.CYAN, "  Checking database connection...")
    cprint(Colors.CYAN, f"    Host:     {DB_HOST}:{DB_PORT}")
    cprint(Colors.CYAN, f"    Database: {DB_NAME}")
    cprint(Colors.CYAN, f"    User:     {DB_USER}")
    cprint(Colors.CYAN, f"    Password: {DB_PASS}")

    # First check if the port is even reachable
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((DB_HOST, DB_PORT))
        sock.close()
    except (ConnectionRefusedError, OSError, socket.timeout):
        sock.close()
        cprint(Colors.RED, f"""
  DATABASE NOT REACHABLE!
  Nothing is listening on {DB_HOST}:{DB_PORT}.

  The database runs in Docker. Make sure:
    1. Docker Desktop is running
    2. Run this to start the container:
       docker run -d --name {DOCKER_CONTAINER} \\
         -e POSTGRES_DB={DB_NAME} \\
         -e POSTGRES_USER={DB_USER} \\
         -e POSTGRES_PASSWORD={DB_PASS} \\
         -p {DB_PORT}:5432 \\
         postgres:16-alpine

  Or if the container exists but is stopped:
       docker start {DOCKER_CONTAINER}
""")
        return False

    # Port is open - try actual psycopg connection if available
    try:
        import psycopg
        conn = psycopg.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER, password=DB_PASS,
            connect_timeout=5,
        )
        conn.close()
        cprint(Colors.GREEN, "    Database connection OK!")
        return True
    except ImportError:
        # psycopg not importable from outside venv, port was open so assume OK
        cprint(Colors.GREEN, "    Port is open, assuming database is ready.")
        return True
    except Exception as e:
        cprint(Colors.RED, f"""
  DATABASE CONNECTION FAILED!
  Port {DB_PORT} is open but couldn't authenticate.

  Tried credentials:
    User:     {DB_USER}
    Password: {DB_PASS}
    Database: {DB_NAME}

  Error: {e}

  Check if the container has the right credentials:
    docker exec {DOCKER_CONTAINER} psql -U {DB_USER} -d {DB_NAME} -c "SELECT 1"
""")
        return False


def find_python():
    """Find python executable (venv preferred)."""
    if sys.platform == "win32":
        venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = BACKEND_DIR / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def main():
    banner()

    # --- Prerequisites ---
    cprint(Colors.CYAN, "  Checking prerequisites...")

    if not check_command("bun"):
        cprint(Colors.RED, "  Bun not found! Install from https://bun.sh/")
        sys.exit(1)
    cprint(Colors.GREEN, "    Bun found")

    if not check_command("docker"):
        cprint(Colors.YELLOW, "    Docker not found (needed for database)")
    else:
        cprint(Colors.GREEN, "    Docker found")

    python_exe = find_python()
    cprint(Colors.GREEN, f"    Python: {python_exe}")

    # --- Database ---
    if not check_database():
        cprint(Colors.YELLOW, "\n  Continuing without database - backend will fail on DB queries.")
        answer = input("  Start anyway? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            sys.exit(1)

    # --- Port checks ---
    cprint(Colors.CYAN, "\n  Checking ports...")
    if not check_port(BACKEND_PORT, "Backend API"):
        sys.exit(1)
    if not check_port(FRONTEND_PORT, "Frontend Dev Server"):
        sys.exit(1)
    cprint(Colors.GREEN, "    All ports clear!")

    # --- Launch ---
    cprint(Colors.CYAN, "\n  Starting servers...\n")

    backend_cmd = [python_exe, "app.py", "runserver", str(BACKEND_PORT)]
    frontend_cmd = ["bun", "run", "dev"]

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                           if sys.platform == "win32" else 0),
        )
        cprint(Colors.GREEN, f"  Backend  -> http://localhost:{BACKEND_PORT}  (PID {backend_proc.pid})")

        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP
                           if sys.platform == "win32" else 0),
        )
        cprint(Colors.GREEN, f"  Frontend -> http://localhost:{FRONTEND_PORT}  (PID {frontend_proc.pid})")

        cprint(Colors.BOLD, "\n  Both servers running. Press Ctrl+C to stop.\n")

        # Wait for either to exit
        while True:
            be_status = backend_proc.poll()
            fe_status = frontend_proc.poll()

            if be_status is not None:
                cprint(Colors.RED, f"\n  Backend exited with code {be_status}")
                frontend_proc.terminate()
                sys.exit(be_status or 1)

            if fe_status is not None:
                cprint(Colors.RED, f"\n  Frontend exited with code {fe_status}")
                backend_proc.terminate()
                sys.exit(fe_status or 1)

            time.sleep(0.5)
    
    # Handle Ctrl+C gracefully to terminate both servers and exit cleanly.
    except KeyboardInterrupt:
        cprint(Colors.YELLOW, "\n\n  Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
            frontend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
            frontend_proc.kill()
        cprint(Colors.GREEN, "  Servers stopped. Bye!\n")
        sys.exit(0)

# If this script is run directly, call the main function to start the application launcher.
if __name__ == "__main__":
    main()
