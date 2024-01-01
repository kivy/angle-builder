import logging
import os
import subprocess
import shutil
import tempfile

from angle_builder.storage import StorageFolderManager


class ANGLE:
    def __init__(
        self,
        branch: str,
        storage_manager: StorageFolderManager,
        revision: str = None,
        logger_level: int = logging.INFO,
    ):
        self.branch = branch
        self.revision = revision
        self.storage_manager = storage_manager
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logger_level)

    @property
    def underlined_branch(self) -> str:
        """
        Returns the branch name with underscores instead of dots or slashes.
        """
        return self.branch.replace(".", "_").replace("/", "__")

    @property
    def angle_path(self) -> os.PathLike:
        """
        Returns the path to our angle folder.
        """
        return os.path.join(
            self.storage_manager.folder_path, f"angle-{self.underlined_branch}"
        )

    def _clone_angle(self):
        """
        Clone ANGLE repository into the storage folder.
        """

        subprocess.run(
            [
                "git",
                "clone",
                "--branch",
                self.branch,
                "--single-branch",
                "https://github.com/google/angle",
                self.angle_path,
            ],
            cwd=self.storage_manager.folder_path,
            check=True,
        )

    def _checkout_revision(self):
        """
        Checkout the specified revision.
        """

        if self.revision is not None:
            subprocess.run(
                ["git", "checkout", self.revision],
                cwd=self.angle_path,
                check=True,
            )

    def clone_and_checkout(self) -> None:
        """
        Clone ANGLE repository and checkout the specified revision.
        """

        self.storage_manager.ensure_folder()

        self._logger.info(
            "Cloning (if needed) ANGLE repository for branch %s", self.branch
        )

        if not os.path.exists(self.angle_path):
            self._clone_angle()

        self._checkout_revision()

    def bootstrap(self) -> None:
        """
        Bootstrap ANGLE.
        """
        self._logger.info(
            "Bootstrapping ANGLE repository for branch %s", self.branch
        )

        subprocess.run(
            ["python", "scripts/bootstrap.py"],
            cwd=self.angle_path,
            check=True,
        )

    def sync(self) -> None:
        """
        Sync ANGLE.
        """
        self._logger.info("Syncing ANGLE repository for branch %s", self.branch)

        subprocess.run(
            ["gclient", "sync"],
            cwd=self.angle_path,
            check=True,
        )

    def _generate_build_targets(self, output_artifact_mode: str) -> None:
        self._logger.info(
            "Generating build targets for branch %s and output_artifact_mode %s",
            self.branch,
            output_artifact_mode,
        )

        builds = []

        common_gn_args = [
            "is_component_build=false",
            "is_debug=false",
        ]

        if output_artifact_mode in ("macos-arm64", "macos-universal"):
            builds.append(
                {
                    "name": "macos-arm64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="arm64"',
                        'target_os="mac"',
                    ],
                }
            )

        if output_artifact_mode in ("macos-x64", "macos-universal"):
            builds.append(
                {
                    "name": "macos-x64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="x64"',
                        'target_os="mac"',
                    ],
                }
            )

        if output_artifact_mode in (
            "iphoneos-arm64",
            "iphone*-universal",
        ):
            builds.append(
                {
                    "name": "iphoneos-arm64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="arm64"',
                        'target_os="ios"',
                        "ios_enable_code_signing=false",
                    ],
                }
            )

        if output_artifact_mode in (
            "iphonesimulator-x64",
            "iphone*-universal",
        ):
            builds.append(
                {
                    "name": "iphonesimulator-x64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="x64"',
                        'target_os="ios"',
                        "ios_enable_code_signing=false",
                    ],
                }
            )

        if output_artifact_mode in (
            "iphonesimulator-arm64",
            "iphone*-universal",
        ):
            builds.append(
                {
                    "name": "iphonesimulator-arm64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="arm64"',
                        'target_os="ios"',
                        "ios_enable_code_signing=false",
                    ],
                }
            )

        return builds

    def _gn_gen(self, build_target: dict) -> None:
        """
        Run gn gen for the specified build target.
        """

        self._logger.info(
            "Running gn gen for branch %s and build target %s",
            self.branch,
            build_target["name"],
        )

        subprocess.run(
            [
                "gn",
                "gen",
                f"out/{build_target['name']}",
                "--args=" + " ".join(build_target["gn_args"]),
            ],
            cwd=self.angle_path,
            check=True,
        )

    def _autoninja_build(self, build_target: dict) -> None:
        """
        Run autoninja for the specified build target.
        """

        self._logger.info(
            "Running autoninja for branch %s and build target %s",
            self.branch,
            build_target["name"],
        )

        subprocess.run(
            [
                "autoninja",
                "-C",
                f"out/{build_target['name']}",
                "libEGL",
                "libGLESv2",
            ],
            cwd=self.angle_path,
            check=True,
        )

    def _create_macos_dylibs(self, output_artifact_mode: str) -> list:
        libEGL_dylib_path = os.path.join(
            self.angle_path, "out", output_artifact_mode, "libEGL.dylib"
        )
        libGLESv2_dylib_path = os.path.join(
            self.angle_path, "out", output_artifact_mode, "libGLESv2.dylib"
        )

        self._logger.info(
            "Creating macos dylibs for branch %s and build target %s",
            self.branch,
            output_artifact_mode,
        )

        if output_artifact_mode == "macos-universal":
            # Ensure the fake macos-universal folder exists (if exists, clean it up)
            macos_universal_folder = os.path.join(
                self.angle_path, "out", "macos-universal"
            )
            if os.path.exists(macos_universal_folder):
                shutil.rmtree(macos_universal_folder)
            os.makedirs(macos_universal_folder)

            self._logger.info(
                "Lipo-ing macos dylibs for branch %s and build target %s",
                self.branch,
                output_artifact_mode,
            )

            # merge x64 and arm64 dylibs into fat dylibs
            subprocess.run(
                [
                    "lipo",
                    "-create",
                    os.path.join(
                        self.angle_path, "out", "macos-x64", "libEGL.dylib"
                    ),
                    os.path.join(
                        self.angle_path, "out", "macos-arm64", "libEGL.dylib"
                    ),
                    "-output",
                    libEGL_dylib_path,
                ],
                cwd=self.angle_path,
                check=True,
            )

            subprocess.run(
                [
                    "lipo",
                    "-create",
                    os.path.join(
                        self.angle_path, "out", "macos-x64", "libGLESv2.dylib"
                    ),
                    os.path.join(
                        self.angle_path, "out", "macos-arm64", "libGLESv2.dylib"
                    ),
                    "-output",
                    libGLESv2_dylib_path,
                ],
                cwd=self.angle_path,
                check=True,
            )

        return [libEGL_dylib_path, libGLESv2_dylib_path]

    def build(self, output_artifact_mode: str, output_folder: str) -> None:
        """
        Build ANGLE for the specified output_artifact_mode.

        The output_artifact_mode could be one of:
        - macos-x64
        - macos-arm64
        - macos-universal
        - iphoneos-arm64
        - iphonesimulator-x64
        - iphonesimulator-arm64
        - iphone*-universal

        The produced artifact is a zip file containing:
        - libEGL
        - libGLESv2
        - include folder
        - LICENSE
        """
        self.clone_and_checkout()
        self.bootstrap()
        self.sync()

        build_targets = self._generate_build_targets(output_artifact_mode)

        for build_target in build_targets:
            self._gn_gen(build_target)

        for build_target in build_targets:
            self._autoninja_build(build_target)

        include_folder_path = os.path.join(self.angle_path, "include")
        license_path = os.path.join(self.angle_path, "LICENSE")

        if output_artifact_mode.startswith("macos"):
            libs = self._create_macos_dylibs(output_artifact_mode)

        with tempfile.TemporaryDirectory() as temp_dir:
            self._logger.info(
                "Creating zip for branch %s and output_artifact_mode %s",
                self.branch,
                output_artifact_mode,
            )
            # Copy libs, include folder and LICENSE to temp_dir
            for lib in libs:
                shutil.copy(lib, temp_dir)

            shutil.copytree(
                include_folder_path, os.path.join(temp_dir, "include")
            )
            shutil.copy(license_path, temp_dir)

            # Create a zip file with libs, include folder and LICENSE
            shutil.make_archive(
                os.path.join(
                    output_folder,
                    f"angle-{self.underlined_branch}-{output_artifact_mode}",
                ),
                "zip",
                root_dir=temp_dir,
                verbose=True,
            )
