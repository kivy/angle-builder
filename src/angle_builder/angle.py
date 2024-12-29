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
            "angle_enable_wgpu=false",
            "mac_deployment_target=\"10.15\"",
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
            "iphoneall-universal",
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
            "iphoneall-universal",
        ):
            builds.append(
                {
                    "name": "iphonesimulator-x64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="x64"',
                        'target_os="ios"',
                        'target_environment="simulator"',
                        "ios_enable_code_signing=false",
                    ],
                }
            )

        if output_artifact_mode in (
            "iphonesimulator-arm64",
            "iphoneall-universal",
        ):
            builds.append(
                {
                    "name": "iphonesimulator-arm64",
                    "gn_args": common_gn_args
                    + [
                        'target_cpu="arm64"',
                        'target_os="ios"',
                        'target_environment="simulator"',
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

            # By using install_name_tool, we can change the dylib's id to @rpath/*.dylib
            subprocess.run(
                [
                    "install_name_tool",
                    "-id",
                    "@rpath/libEGL.dylib",
                    libEGL_dylib_path,
                ],
                check=True,
            )

            subprocess.run(
                [
                    "install_name_tool",
                    "-id",
                    "@rpath/libGLESv2.dylib",
                    libGLESv2_dylib_path,
                ],
                check=True,
            )

        return [libEGL_dylib_path, libGLESv2_dylib_path]

    def _patch_frameworks_plist(self, framework_path: str) -> None:
        # The Info.plist file is missing CFBundleShortVersionString which
        # is required for the framework to be accepted by the App Store.
        # We need to patch the Info.plist file to add the missing key.

        self._logger.info("Patching Info.plist files for iphoneos frameworks")

        subprocess.run(
            [
                "plutil",
                "-replace",
                "CFBundleShortVersionString",
                "-string",
                "1.0",
                os.path.join(framework_path, "Info.plist"),
            ],
            check=True,
        )

    def _create_iphoneos_frameworks(self, output_artifact_mode: str) -> list:

        output_extension = (
            "xcframework"
            if output_artifact_mode == "iphoneall-universal"
            else "framework"
        )

        libEGL_output_path = os.path.join(
            self.angle_path,
            "out",
            output_artifact_mode,
            f"libEGL.{output_extension}",
        )
        libGLESv2_output_path = os.path.join(
            self.angle_path,
            "out",
            output_artifact_mode,
            f"libGLESv2.{output_extension}",
        )

        self._logger.info(
            "Creating iphoneos frameworks for branch %s and build target %s",
            self.branch,
            output_artifact_mode,
        )

        if output_artifact_mode == "iphoneall-universal":

            # Ensure the fake all-universal folder exists
            # and is empty
            iphone_universal_folder = os.path.join(
                self.angle_path, "out", "iphoneos-arm64", "iphoneall-universal"
            )
            shutil.rmtree(iphone_universal_folder, ignore_errors=True)
            os.makedirs(iphone_universal_folder)

            # Ensure the fake iphonesimulator-universal folder exists,
            # and is empty
            iphonesimulator_universal_folder = os.path.join(
                self.angle_path, "out", "iphonesimulator-universal"
            )
            shutil.rmtree(iphonesimulator_universal_folder, ignore_errors=True)
            os.makedirs(iphonesimulator_universal_folder)

            self._logger.info(
                "Lipo-ing iphonesimulator frameworks for branch %s and build target %s",
                self.branch,
                output_artifact_mode,
            )

            # Copy iphonesimulator-x64 frameworks to iphonesimulator-universal
            # (But do not keep the binary files)
            shutil.copytree(
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-x64",
                    "libEGL.framework",
                ),
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-universal",
                    "libEGL.framework",
                ),
            )
            os.remove(
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-universal",
                    "libEGL.framework",
                    "libEGL",
                )
            )
            shutil.copytree(
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-x64",
                    "libGLESv2.framework",
                ),
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-universal",
                    "libGLESv2.framework",
                ),
            )
            os.remove(
                os.path.join(
                    self.angle_path,
                    "out",
                    "iphonesimulator-universal",
                    "libGLESv2.framework",
                    "libGLESv2",
                )
            )
            # Lipo-ize iphonesimulator frameworks into fat frameworks
            subprocess.run(
                [
                    "lipo",
                    "-create",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-x64",
                        "libEGL.framework",
                        "libEGL",
                    ),
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-arm64",
                        "libEGL.framework",
                        "libEGL",
                    ),
                    "-output",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-universal",
                        "libEGL.framework",
                        "libEGL",
                    ),
                ],
                cwd=self.angle_path,
                check=True,
            )

            subprocess.run(
                [
                    "lipo",
                    "-create",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-x64",
                        "libGLESv2.framework",
                        "libGLESv2",
                    ),
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-arm64",
                        "libGLESv2.framework",
                        "libGLESv2",
                    ),
                    "-output",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-universal",
                        "libGLESv2.framework",
                        "libGLESv2",
                    ),
                ],
                cwd=self.angle_path,
                check=True,
            )

            # Create an xcframework for libEGL
            subprocess.run(
                [
                    "xcodebuild",
                    "-create-xcframework",
                    "-framework",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphoneos-arm64",
                        "libEGL.framework",
                    ),
                    "-framework",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-universal",
                        "libEGL.framework",
                    ),
                    "-output",
                    libEGL_output_path,
                ],
                cwd=self.angle_path,
                check=True,
            )

            # Create an xcframework for libGLESv2
            subprocess.run(
                [
                    "xcodebuild",
                    "-create-xcframework",
                    "-framework",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphoneos-arm64",
                        "libGLESv2.framework",
                    ),
                    "-framework",
                    os.path.join(
                        self.angle_path,
                        "out",
                        "iphonesimulator-universal",
                        "libGLESv2.framework",
                    ),
                    "-output",
                    libGLESv2_output_path,
                ],
                cwd=self.angle_path,
                check=True,
            )

        return [libEGL_output_path, libGLESv2_output_path]

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
        - iphoneall-universal

        The produced artifact is a .tar.gz archive containing:
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
            if build_target["name"].startswith("iphone"):
                self._patch_frameworks_plist(
                    os.path.join(
                        self.angle_path,
                        "out",
                        build_target["name"],
                        "libEGL.framework",
                    )
                )
                self._patch_frameworks_plist(
                    os.path.join(
                        self.angle_path,
                        "out",
                        build_target["name"],
                        "libGLESv2.framework",
                    )
                )

        include_folder_path = os.path.join(self.angle_path, "include")
        license_path = os.path.join(self.angle_path, "LICENSE")

        if output_artifact_mode.startswith("macos"):
            libs = self._create_macos_dylibs(output_artifact_mode)
        elif output_artifact_mode.startswith("iphone"):
            libs = self._create_iphoneos_frameworks(output_artifact_mode)

        with tempfile.TemporaryDirectory() as temp_dir:
            self._logger.info(
                "Creating archive for branch %s and output_artifact_mode %s",
                self.branch,
                output_artifact_mode,
            )
            # Copy libs, include folder and LICENSE to temp_dir
            for lib in libs:
                if os.path.isdir(lib):
                    shutil.copytree(
                        lib, os.path.join(temp_dir, os.path.basename(lib))
                    )
                else:
                    shutil.copy(lib, temp_dir)

            shutil.copytree(
                include_folder_path, os.path.join(temp_dir, "include")
            )
            shutil.copy(license_path, temp_dir)

            # Create a .tar.gz archive with libs, include folder and LICENSE
            shutil.make_archive(
                os.path.join(output_folder, f"angle-{output_artifact_mode}"),
                "gztar",
                root_dir=temp_dir,
                verbose=True,
            )
