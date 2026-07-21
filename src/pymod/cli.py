import argparse
import os
import sys

from . import __version__, installer, manifest, venv


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pymod",
        description="Python Module Manager",
    )
    parser.add_argument("--version", action="version", version=f"pymod {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize pymod.json and .venv")

    sub.add_parser("install", help="Install all dependencies from manifest")

    add_p = sub.add_parser("add", help="Add a dependency")
    add_p.add_argument("name", help="Package name")
    add_p.add_argument("target", nargs="?", help="Version, git URL, or local path")
    add_p.add_argument("ref", nargs="?", help="Git ref (branch/tag/commit)")

    rm_p = sub.add_parser("remove", help="Remove a dependency")
    rm_p.add_argument("name", help="Package name")

    up_p = sub.add_parser("update", help="Update dependencies")
    up_p.add_argument("name", nargs="?", help="Specific package to update")

    sub.add_parser("list", help="List installed dependencies")

    sub.add_parser("clean", help="Remove .venv directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        _dispatch(args)
    except (manifest.ManifestError, installer.InstallError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "init":
        _cmd_init()
    elif cmd == "install":
        _cmd_install()
    elif cmd == "add":
        _cmd_add(args.name, args.target, args.ref)
    elif cmd == "remove":
        _cmd_remove(args.name)
    elif cmd == "update":
        _cmd_update(args.name)
    elif cmd == "list":
        _cmd_list()
    elif cmd == "clean":
        _cmd_clean()


def _cmd_init() -> None:
    if manifest.exists():
        print(f"{manifest.MANIFEST_NAME} already exists")
    else:
        manifest.create_empty()
        print(f"created {manifest.MANIFEST_NAME}")
    if venv.exists():
        print(".venv already exists")
    else:
        venv.create()
        print("created .venv")


def _cmd_install() -> None:
    installer.install_all()
    data = manifest.load()
    count = len(data["dependencies"])
    print(f"installed {count} {'dependency' if count == 1 else 'dependencies'}")


def _cmd_add(name: str, target: str | None, ref: str | None) -> None:
    dep = _parse_add_args(name, target, ref)
    if manifest.exists():
        data = manifest.load()
    else:
        data = {"dependencies": []}
    data = manifest.add_dependency(data, dep)
    manifest.save(data)
    installer.install_dep(dep)
    print(f"added and installed '{name}' ({dep['type']})")


def _parse_add_args(name: str, target: str | None, ref: str | None) -> dict:
    if target is None:
        return {"name": name, "type": "pip"}
    if target.startswith(("http://", "https://", "git@", "git://")):
        dep: dict = {"name": name, "type": "git", "url": target}
        if ref:
            dep["ref"] = ref
        return dep
    if os.path.exists(target) or target.startswith(("./", "../")):
        return {"name": name, "type": "local", "path": target}
    return {"name": name, "type": "pip", "version": target}


def _cmd_remove(name: str) -> None:
    data = manifest.load()
    dep = manifest.find_dependency(data, name)
    if dep is None:
        print(f"'{name}' not in manifest")
        return
    installer.uninstall(name)
    data = manifest.remove_dependency(data, name)
    manifest.save(data)
    print(f"removed '{name}'")


def _cmd_update(name: str | None) -> None:
    if name:
        installer.update_one(name)
        print(f"updated '{name}'")
    else:
        installer.update_all()
        data = manifest.load()
        count = len(data["dependencies"])
        print(f"updated {count} {'dependency' if count == 1 else 'dependencies'}")


def _cmd_list() -> None:
    data = manifest.load()
    installed = installer.list_installed()
    for dep in data["dependencies"]:
        status = "installed" if dep["name"].lower() in installed else "missing"
        ver = dep.get("version") or dep.get("ref") or dep.get("path") or ""
        line = f"  {dep['name']}"
        if ver:
            line += f" ({ver})"
        print(f"{line} [{status}]")


def _cmd_clean() -> None:
    if venv.exists():
        venv.remove()
        print("removed .venv")
    else:
        print(".venv does not exist")
