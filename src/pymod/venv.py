import os
import shutil
import subprocess
import sys

VENV_DIR = ".venv"


def venv_path(root: str = ".") -> str:
    return os.path.join(root, VENV_DIR)


def exists(root: str = ".") -> bool:
    path = venv_path(root)
    return os.path.isdir(path) and os.path.isfile(os.path.join(path, "pyvenv.cfg"))


def python_exe(root: str = ".") -> str:
    path = venv_path(root)
    if sys.platform == "win32":
        return os.path.join(path, "Scripts", "python.exe")
    return os.path.join(path, "bin", "python")


def pip_exe(root: str = ".") -> str:
    path = venv_path(root)
    if sys.platform == "win32":
        return os.path.join(path, "Scripts", "pip.exe")
    return os.path.join(path, "bin", "pip")


def create(root: str = ".") -> None:
    if exists(root):
        return
    subprocess.run(
        [sys.executable, "-m", "venv", venv_path(root)],
        check=True,
        capture_output=True,
    )


def remove(root: str = ".") -> None:
    path = venv_path(root)
    if os.path.isdir(path):
        shutil.rmtree(path)
