import os
import tempfile
import shutil
from unittest import mock

import pytest

from angle_builder.depot_tools import DepotTools
from angle_builder.storage import StorageFolderManager


@pytest.fixture
def depot_tools(request):
    _tmpdir = tempfile.mkdtemp()
    _storage_manager = StorageFolderManager(
        user_path=os.path.join(_tmpdir, "storage")
    )
    _depot_tools = DepotTools(storage_manager=_storage_manager)

    def finalizer():
        shutil.rmtree(_tmpdir)

    request.addfinalizer(finalizer)

    return _depot_tools


def test_depot_tools_path(depot_tools):
    expected_path = os.path.join(
        depot_tools.storage_manager.folder_path, "depot_tools"
    )
    assert depot_tools.depot_tools_path == expected_path


def test_ensure_depot_tools_cloned(depot_tools):
    # Just check that the folder exists
    with mock.patch(
        "angle_builder.depot_tools.DepotTools._clone_darwin_linux"
    ) as _m__clone_darwin_linux:
        depot_tools.ensure_depot_tools()
        _m__clone_darwin_linux.assert_called_once()


def test_ensure_depot_tools_is_in_path(depot_tools):
    with mock.patch(
        "angle_builder.depot_tools.DepotTools._clone_darwin_linux"
    ) as _m__clone_darwin_linux:
        depot_tools.ensure_depot_tools()
        _m__clone_darwin_linux.assert_called_once()
    _path_content = os.environ["PATH"].split(os.pathsep)
    assert depot_tools.depot_tools_path in _path_content
