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
        self.storage_folder_name = ".angle-builder"

        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logger_level)

        if user_path is None:
            self.folder_path = os.path.join(
                os.path.expanduser("~"), self.storage_folder_name
            )
        else:
            self.folder_path = os.path.join(user_path, self.storage_folder_name)

    def ensure_folder(self) -> None:
        """
        Ensures that the build folder exists.
        If it does not exist, it creates it.
        """
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)
            self._logger.info(
                "Build folder '%s' created at '%s'",
                self.storage_folder_name,
                self.folder_path,
            )
        else:
            self._logger.info(
                "Build folder '%s' already exists at '%s'",
                self.storage_folder_name,
                self.folder_path,
            )

    def delete_folder(self) -> None:
        """
        Deletes the build folder.
        """
        if os.path.exists(self.folder_path):
            os.rmdir(self.folder_path)
            self._logger.info(
                "Build folder '%s' deleted from '%s'",
                self.storage_folder_name,
                self.folder_path,
            )
        else:
            self._logger.info(
                "Build folder '%s' does not exist at '%s'",
                self.storage_folder_name,
                self.folder_path,
            )
