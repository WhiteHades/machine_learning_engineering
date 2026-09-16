"""Copy the existing editor configuration and plugins into book-owned storage."""
import os
from pathlib import Path
import shutil
import sys
import tempfile

target = Path(sys.argv[1])
config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "nvim"
data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "nvim"
if not (config / "init.lua").is_file() or not (data / "lazy/lazy.nvim").is_dir():
    sys.exit("An existing LazyVim configuration and installed plugins are required.")
excluded = shutil.ignore_patterns(".venv", "__pycache__", "*.log", ".env*", "*.pem", "*.key",
                                 "credentials*", "id_rsa*", "id_ed25519*")


def snapshot(source, destination, roots):
    def ignore(directory, names):
        skipped = excluded(directory, names)
        for name in set(names) - set(skipped):
            path = Path(directory) / name
            if path.is_symlink() and not any(path.resolve().is_relative_to(root) for root in roots):
                raise ValueError(f"snapshot link leaves the editor source: {path}")
        return skipped

    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=destination.parent) as stage:
            copied = Path(stage) / "snapshot"
            shutil.copytree(source, copied, ignore=ignore)
            copied.rename(destination)


snapshot(config, target / "config/nvim", [config.resolve(), (config / "init.lua").resolve().parent])
snapshot(data / "lazy", target / "data/nvim/lazy",
         [(data / "lazy").resolve()] + [p.resolve() for p in (data / "lazy").iterdir() if p.is_dir()])
# Reuse existing parser binaries and queries; setup checks container compatibility.
def copy_missing(source, destination):
    if not Path(destination).exists():
        shutil.copy2(source, destination)
    return destination

for name in ("parser", "parser-info"):
    if (data / "site" / name).is_dir():
        shutil.copytree(data / "site" / name, target / "data/nvim/site" / name,
                        dirs_exist_ok=True, copy_function=copy_missing)
theme = Path.home() / ".local/state/omarchy/current/theme/neovim.lua"
theme_copy = target / "home/.local/state/omarchy/current/theme/neovim.lua"
if theme.is_file() and not theme_copy.exists():
    theme_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(theme, theme_copy)
print(f"Isolated editor snapshot ready in {target}")
