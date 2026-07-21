import os
import subprocess
from typing import Any

from . import venv


class InstallError(Exception):
    pass


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise InstallError(result.stderr.strip() or f"command failed: {' '.join(cmd)}")
    return result


def install_all(root: str = ".") -> None:
    from .manifest import load

    venv.create(root)
    data = load(root)
    for dep in data["dependencies"]:
        install_dep(dep, root)


def install_dep(dep: dict[str, Any], root: str = ".") -> None:
    dtype = dep["type"]
    name = dep["name"]
    if dtype == "pip":
        _install_pip(dep, root)
    elif dtype == "git":
        _install_git(dep, root)
    elif dtype == "local":
        _install_local(dep, root)
    else:
        raise InstallError(f"unknown type '{dtype}' for '{name}'")


def _install_pip(dep: dict[str, Any], root: str = ".") -> None:
    name = dep["name"]
    version = dep.get("version")
    spec = f"{name}=={version}" if version else name
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    _run([pip, "install", spec])


def _install_git(dep: dict[str, Any], root: str = ".") -> None:
    url = dep["url"]
    ref = dep.get("ref")
    subdir = dep.get("dir")
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    spec = f"git+{url}"
    if ref:
        spec += f"@{ref}"
    if subdir:
        spec += f"#subdirectory={subdir}"
    _run([pip, "install", spec])


def _install_local(dep: dict[str, Any], root: str = ".") -> None:
    path = dep["path"]
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.exists(path):
        raise InstallError(f"local path '{dep['path']}' does not exist")
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    _run([pip, "install", path])


def uninstall(name: str, root: str = ".") -> None:
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    _run([pip, "uninstall", "-y", name])


def update_all(root: str = ".") -> None:
    from .manifest import load

    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    data = load(root)
    for dep in data["dependencies"]:
        if dep["type"] == "pip":
            _run([pip, "install", "--upgrade", dep["name"]])
        else:
            install_dep(dep, root)


def update_one(name: str, root: str = ".") -> None:
    from . import manifest

    data = manifest.load(root)
    dep = manifest.find_dependency(data, name)
    if dep is None:
        raise InstallError(f"dependency '{name}' not found in manifest")
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    if dep["type"] == "pip":
        _run([pip, "install", "--upgrade", dep["name"]])
    else:
        install_dep(dep, root)


def list_installed(root: str = ".") -> list[str]:
    pip = venv.pip_exe(root)
    if not os.path.isfile(pip):
        raise InstallError("pip not found, did you run 'pymod init'?")
    result = _run([pip, "list", "--format=freeze"])
    packages = []
    for line in result.stdout.strip().splitlines():
        if "==" in line:
            packages.append(line.split("==")[0].lower())
    return packages
