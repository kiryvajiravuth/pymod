import json
import os
from typing import Any

MANIFEST_NAME = "pymod.json"
VALID_TYPES = ("pip", "git", "local")


class ManifestError(Exception):
    pass


def manifest_path(root: str = ".") -> str:
    return os.path.join(root, MANIFEST_NAME)


def exists(root: str = ".") -> bool:
    return os.path.isfile(manifest_path(root))


def load(root: str = ".") -> dict[str, Any]:
    path = manifest_path(root)
    if not os.path.isfile(path):
        raise ManifestError(f"{MANIFEST_NAME} not found in {os.path.abspath(root)}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate(data)
    return data


def save(data: dict[str, Any], root: str = ".") -> None:
    validate(data)
    path = manifest_path(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def create_empty(root: str = ".") -> None:
    if exists(root):
        raise ManifestError(f"{MANIFEST_NAME} already exists")
    save({"dependencies": []}, root)


def validate(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    deps = data.get("dependencies")
    if deps is None:
        raise ManifestError("missing 'dependencies' key")
    if not isinstance(deps, list):
        raise ManifestError("'dependencies' must be an array")
    for i, dep in enumerate(deps):
        _validate_dep(dep, i)


def _validate_dep(dep: Any, index: int) -> None:
    if not isinstance(dep, dict):
        raise ManifestError(f"dependency #{index} must be an object")
    name = dep.get("name")
    dtype = dep.get("type")
    if not name or not isinstance(name, str):
        raise ManifestError(f"dependency #{index} missing valid 'name'")
    if dtype not in VALID_TYPES:
        raise ManifestError(
            f"dependency #{index} ('{name}') has invalid type '{dtype}', "
            f"must be one of: {', '.join(VALID_TYPES)}"
        )
    if dtype == "pip":
        pass
    elif dtype == "git":
        if not dep.get("url"):
            raise ManifestError(f"dependency #{index} ('{name}') missing 'url' for git type")
    elif dtype == "local":
        if not dep.get("path"):
            raise ManifestError(f"dependency #{index} ('{name}') missing 'path' for local type")


def add_dependency(data: dict[str, Any], dep: dict[str, Any]) -> dict[str, Any]:
    _validate_dep(dep, len(data["dependencies"]))
    name = dep["name"]
    for existing in data["dependencies"]:
        if existing.get("name") == name:
            raise ManifestError(f"dependency '{name}' already exists")
    data["dependencies"].append(dep)
    return data


def remove_dependency(data: dict[str, Any], name: str) -> dict[str, Any]:
    original_len = len(data["dependencies"])
    data["dependencies"] = [d for d in data["dependencies"] if d.get("name") != name]
    if len(data["dependencies"]) == original_len:
        raise ManifestError(f"dependency '{name}' not found")
    return data


def find_dependency(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    for dep in data["dependencies"]:
        if dep.get("name") == name:
            return dep
    return None
