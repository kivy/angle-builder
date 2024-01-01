import logging
import os


class StorageFolderManager:
    """
    Ensures that the storage folder exists, and provides methods
    to control the lifecycle of the storage folder.
    """

    def __init__(self, user_path: str = None, logger_level: int = logging.INFO):
        """
        Args:
            user_path (str): Path to the storage folder, if None, it will be
                created in the user's home directory.
            logger_level (int): Logging level.
        """
        self.user_path = user_path

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logger_level)

    @property
    def folder_path(self) -> os.PathLike:
        """
        Returns the path to our storage folder.
        """
        if self.user_path:
            return self.user_path
        else:
            return os.path.join(os.path.expanduser("~"), ".angle-builder")

    def ensure_folder(self) -> None:
        """
        Ensures that the build folder exists.
        If it does not exist, it creates it.
        """
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
            self._logger.info("Created build folder at '%s'", self.folder_path)
        else:
            self._logger.info(
                "Build folder already exists at '%s'", self.folder_path
            )

    def delete_folder(self) -> None:
        """
        Deletes the build folder.
        """
        if os.path.exists(self.folder_path):
            os.rmdir(self.folder_path)
            self._logger.info("Deleted build folder at '%s'", self.folder_path)
        else:
            self._logger.info(
                "Build folder does not exist at '%s'", self.folder_path
            )
