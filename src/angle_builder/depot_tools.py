import logging
import os
import subprocess

from angle_builder.storage import StorageFolderManager


class DepotTools:
    def __init__(
        self,
        storage_manager: StorageFolderManager,
        logger_level: int = logging.INFO,
    ):
        """
        Args:
            storage_manager (StorageFolderManager): Storage folder manager.
            logger_level (int): Logging level.
        """
        self.storage_manager = storage_manager
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logger_level)

    @property
    def depot_tools_path(self) -> os.PathLike:
        """
        Returns the path to our depot_tools folder.
        """
        return os.path.join(self.storage_manager.folder_path, "depot_tools")

    def _clone_darwin_linux(self):
        """
        Clones depot_tools into our storage folder for Linux and macOS.
        """
        self._logger.info(
            "Cloning depot_tools into '%s'", self.depot_tools_path
        )

        subprocess.run(
            [
                "git",
                "clone",
                "https://chromium.googlesource.com/chromium/tools/depot_tools.git",
                self.depot_tools_path,
            ],
            check=True,
        )

    def _ensure_depot_tools_is_in_path(self):
        _path_content = os.environ["PATH"].split(os.pathsep)

        if self.depot_tools_path not in _path_content:
            os.environ["PATH"] = os.pathsep.join(
                [self.depot_tools_path, os.environ["PATH"]]
            )

    def ensure_depot_tools(self) -> None:
        """
        Ensures that depot_tools is downloaded and in the path.
        """
        self._logger.info("Ensuring depot_tools is available and in PATH")

        if not os.path.exists(self.depot_tools_path):
            self._clone_darwin_linux()

        self._ensure_depot_tools_is_in_path()
