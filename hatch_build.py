from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        bin_dir = Path("src/netscope/bin")
        has_binary = bin_dir.exists() and any(bin_dir.iterdir())
        if has_binary:
            build_data["pure_python"] = False
