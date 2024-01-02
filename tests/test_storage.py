import os
import tempfile
import shutil

import pytest

from angle_builder.storage import StorageFolderManager


@pytest.fixture
def storage_manager(request):
    _tmpdir = tempfile.mkdtemp()
    _storage_manager = StorageFolderManager(
        user_path=os.path.join(_tmpdir, "storage")
    )

    def finalizer():
        shutil.rmtree(_tmpdir)

    request.addfinalizer(finalizer)

    return _storage_manager


def test_ensure_folder_not_exists(storage_manager):
    """
    Ensure that the storage folder is created if it does not exist.
    """
    assert os.path.exists(storage_manager.folder_path) is False
    storage_manager.ensure_folder()
    assert os.path.exists(storage_manager.folder_path) is True


def test_ensure_folder_exists(storage_manager):
    """
    Ensure that the storage folder is kept if it exists.
    """
    assert os.path.exists(storage_manager.folder_path) is False
    storage_manager.ensure_folder()
    assert os.path.exists(storage_manager.folder_path) is True
    storage_manager.ensure_folder()
    assert os.path.exists(storage_manager.folder_path) is True


def test_delete_folder(storage_manager):
    """
    Ensure that the storage folder is deleted.
    """
    assert os.path.exists(storage_manager.folder_path) is False
    storage_manager.ensure_folder()
    assert os.path.exists(storage_manager.folder_path) is True
    storage_manager.delete_folder()
    assert os.path.exists(storage_manager.folder_path) is False


def test_delete_not_existing_folder(storage_manager):
    """
    Ensure that the storage folder is not deleted if it does not exist.
    """
    assert os.path.exists(storage_manager.folder_path) is False
    storage_manager.delete_folder()
    assert os.path.exists(storage_manager.folder_path) is False
