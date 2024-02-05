import os
import tempfile
import shutil

import pytest

from angle_builder.angle import ANGLE
from angle_builder.storage import StorageFolderManager
from angle_builder.depot_tools import DepotTools


@pytest.fixture
def angle(request):
    _tmpdir = tempfile.mkdtemp()
    _storage_manager = StorageFolderManager(
        user_path=os.path.join(_tmpdir, "storage")
    )

    _depot_tools = DepotTools(storage_manager=_storage_manager)
    _depot_tools.ensure_depot_tools()
    _angle = ANGLE(
        branch="chromium/6045",
        storage_manager=_storage_manager,
    )

    def finalizer():
        shutil.rmtree(_tmpdir)

    request.addfinalizer(finalizer)

    return _angle


def test_underlined_branch_name(angle):
    assert angle.underlined_branch == "chromium__6045"


def test_angle_path(angle):
    assert angle.angle_path == os.path.join(
        angle.storage_manager.folder_path, f"angle-{angle.underlined_branch}"
    )


def test_generate_build_targets_mac_universal(angle):

    _x64_macos = angle._generate_build_targets("macos-x64")
    _arm64_macos = angle._generate_build_targets("macos-arm64")

    assert len(_x64_macos) == 1
    assert len(_arm64_macos) == 1

    _universal_macos = angle._generate_build_targets("macos-universal")

    assert len(_universal_macos) == 2
    assert _x64_macos[0] in _universal_macos
    assert _arm64_macos[0] in _universal_macos


def test_generate_build_targets_ios_universal(angle):

    x64_iphonesimulator = angle._generate_build_targets("iphonesimulator-x64")
    arm64_iphonesimulator = angle._generate_build_targets("iphonesimulator-arm64")
    arm64_iphoneos = angle._generate_build_targets("iphoneos-arm64")

    assert len(x64_iphonesimulator) == 1
    assert len(arm64_iphonesimulator) == 1
    assert len(arm64_iphoneos) == 1

    universal_all_iphone = angle._generate_build_targets("iphoneall-universal")

    assert len(universal_all_iphone) == 3
    assert x64_iphonesimulator[0] in universal_all_iphone
    assert arm64_iphonesimulator[0] in universal_all_iphone
    assert arm64_iphoneos[0] in universal_all_iphone
