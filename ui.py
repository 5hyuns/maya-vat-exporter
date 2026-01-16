# -*- coding: utf-8 -*-
"""
Maya VAT - User Interface
"""

import maya.cmds as cmds
from maya import OpenMayaUI as omui

try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance

from . import core, utils

# Window instance
_window = None


def get_maya_main_window():
    """Get Maya main window as Qt widget"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class OpenVATWindow(QtWidgets.QDialog):
    """Main Maya VAT window"""

    WINDOW_TITLE = "Maya VAT"

    def __init__(self, parent=get_maya_main_window()):
        super(OpenVATWindow, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(350)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        """Create UI widgets"""
        # Mesh selection
        self.mesh_label = QtWidgets.QLabel("Target Mesh:")
        self.mesh_line = QtWidgets.QLineEdit()
        self.mesh_line.setReadOnly(True)
        self.mesh_line.setPlaceholderText("Select a mesh...")
        self.mesh_btn = QtWidgets.QPushButton("<<")
        self.mesh_btn.setFixedWidth(30)
        self.mesh_btn.setToolTip("Get selected mesh")

        # Frame range
        self.frame_label = QtWidgets.QLabel("Frame Range:")
        self.frame_start = QtWidgets.QSpinBox()
        self.frame_start.setRange(-10000, 10000)
        self.frame_end = QtWidgets.QSpinBox()
        self.frame_end.setRange(-10000, 10000)
        self.frame_btn = QtWidgets.QPushButton("Timeline")
        self.frame_btn.setToolTip("Get from timeline")

        # Skip first frame option
        self.skip_first_check = QtWidgets.QCheckBox("Skip First Frame")
        self.skip_first_check.setToolTip(
            "Use first frame as proxy reference only.\n"
            "The first frame will NOT be included in the texture.\n"
            "Useful when first frame is T-Pose or bind pose."
        )

        # Set default frame range
        start, end = utils.get_frame_range()
        self.frame_start.setValue(start)
        self.frame_end.setValue(end)

        # Output directory
        self.output_label = QtWidgets.QLabel("Output Directory:")
        self.output_line = QtWidgets.QLineEdit()
        self.output_line.setPlaceholderText("Select output folder...")
        self.output_btn = QtWidgets.QPushButton("...")
        self.output_btn.setFixedWidth(30)

        # Options
        self.options_group = QtWidgets.QGroupBox("Options")
        self.normals_check = QtWidgets.QCheckBox("Export Normals (separate texture)")
        self.export_mesh_check = QtWidgets.QCheckBox("Export Mesh (FBX)")
        self.export_mesh_check.setChecked(True)

        # Coordinate Space
        self.space_label = QtWidgets.QLabel("Coordinate Space:")
        self.space_combo = QtWidgets.QComboBox()
        self.space_combo.addItem("Object (Local) - Recommended", False)
        self.space_combo.addItem("World", True)
        self.space_combo.setCurrentIndex(0)  # Default to Object space
        self.space_combo.setToolTip(
            "Object: Use for characters with runtime movement (recommended)\n"
            "World: Use only if mesh transform is fixed"
        )

        # Info display
        self.info_group = QtWidgets.QGroupBox("Info")
        self.info_verts = QtWidgets.QLabel("Vertices: -")
        self.info_frames = QtWidgets.QLabel("Frames: -")
        self.info_size = QtWidgets.QLabel("Texture Size: -")

        # VAT UV Group
        self.uv_group = QtWidgets.QGroupBox("VAT UV")
        self.uv_set_label = QtWidgets.QLabel("UV Set Name:")
        self.uv_set_line = QtWidgets.QLineEdit("VAT_UV")
        self.uv_set_line.setToolTip("Name for the VAT UV set (default: VAT_UV)")
        self.uv_force_check = QtWidgets.QCheckBox("Overwrite if exists")
        self.uv_force_check.setToolTip("If checked, overwrite existing UV set with same name")
        self.create_uv_btn = QtWidgets.QPushButton("Create VAT UV")
        self.create_uv_btn.setToolTip(
            "Create VAT UV set on the selected mesh.\n"
            "Each vertex gets a unique U coordinate for texture lookup."
        )
        self.uv_status_label = QtWidgets.QLabel("Status: -")

        # Encode button
        self.encode_btn = QtWidgets.QPushButton("Encode VAT")
        self.encode_btn.setMinimumHeight(40)
        self.encode_btn.setEnabled(False)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)

        # Credit label
        self.credit_label = QtWidgets.QLabel("powered by 555hyuns@gmail.com")
        self.credit_label.setStyleSheet("color: gray; font-size: 10px;")
        self.credit_label.setAlignment(QtCore.Qt.AlignCenter)

    def create_layouts(self):
        """Create layouts"""
        main_layout = QtWidgets.QVBoxLayout(self)

        # Mesh selection layout
        mesh_layout = QtWidgets.QHBoxLayout()
        mesh_layout.addWidget(self.mesh_label)
        mesh_layout.addWidget(self.mesh_line)
        mesh_layout.addWidget(self.mesh_btn)
        main_layout.addLayout(mesh_layout)

        # Frame range layout
        frame_layout = QtWidgets.QHBoxLayout()
        frame_layout.addWidget(self.frame_label)
        frame_layout.addWidget(self.frame_start)
        frame_layout.addWidget(QtWidgets.QLabel("-"))
        frame_layout.addWidget(self.frame_end)
        frame_layout.addWidget(self.frame_btn)
        frame_layout.addWidget(self.skip_first_check)
        main_layout.addLayout(frame_layout)

        # Output layout
        output_layout = QtWidgets.QHBoxLayout()
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(self.output_btn)
        main_layout.addLayout(output_layout)

        # Options layout
        options_layout = QtWidgets.QVBoxLayout()
        options_layout.addWidget(self.normals_check)
        options_layout.addWidget(self.export_mesh_check)

        # Coordinate space layout (inside options)
        space_layout = QtWidgets.QHBoxLayout()
        space_layout.addWidget(self.space_label)
        space_layout.addWidget(self.space_combo)
        options_layout.addLayout(space_layout)

        self.options_group.setLayout(options_layout)
        main_layout.addWidget(self.options_group)

        # Info layout
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.addWidget(self.info_verts)
        info_layout.addWidget(self.info_frames)
        info_layout.addWidget(self.info_size)
        self.info_group.setLayout(info_layout)
        main_layout.addWidget(self.info_group)

        # VAT UV layout
        uv_layout = QtWidgets.QVBoxLayout()
        uv_name_layout = QtWidgets.QHBoxLayout()
        uv_name_layout.addWidget(self.uv_set_label)
        uv_name_layout.addWidget(self.uv_set_line)
        uv_layout.addLayout(uv_name_layout)
        uv_layout.addWidget(self.uv_force_check)
        uv_layout.addWidget(self.create_uv_btn)
        uv_layout.addWidget(self.uv_status_label)
        self.uv_group.setLayout(uv_layout)
        main_layout.addWidget(self.uv_group)

        # Encode button
        main_layout.addWidget(self.encode_btn)
        main_layout.addWidget(self.progress_bar)

        # Spacer
        main_layout.addStretch()

        # Credit
        main_layout.addWidget(self.credit_label)

    def create_connections(self):
        """Create signal connections"""
        self.mesh_btn.clicked.connect(self.get_selected_mesh)
        self.frame_btn.clicked.connect(self.get_timeline_range)
        self.output_btn.clicked.connect(self.browse_output)
        self.encode_btn.clicked.connect(self.encode_vat)
        self.create_uv_btn.clicked.connect(self.create_vat_uv)

        self.mesh_line.textChanged.connect(self.update_info)
        self.frame_start.valueChanged.connect(self.update_info)
        self.frame_end.valueChanged.connect(self.update_info)
        self.skip_first_check.stateChanged.connect(self.update_info)
        self.output_line.textChanged.connect(self.validate_inputs)

    def get_selected_mesh(self):
        """Get selected mesh from scene"""
        mesh = utils.get_selected_mesh()
        if mesh:
            self.mesh_line.setText(mesh)
        else:
            cmds.warning("Please select a mesh object")

    def get_timeline_range(self):
        """Get frame range from timeline"""
        start, end = utils.get_frame_range()
        self.frame_start.setValue(start)
        self.frame_end.setValue(end)

    def browse_output(self):
        """Browse for output directory"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        if directory:
            self.output_line.setText(directory)

    def update_info(self):
        """Update info display"""
        mesh_name = self.mesh_line.text()

        if mesh_name and cmds.objExists(mesh_name):
            num_verts = utils.get_vertex_count(mesh_name)
            num_frames = self.frame_end.value() - self.frame_start.value() + 1
            skip_first = self.skip_first_check.isChecked()

            # Texture frames (skip first frame if checked)
            texture_frames = num_frames - 1 if skip_first else num_frames

            self.info_verts.setText("Vertices: {}".format(num_verts))
            self.info_frames.setText("Frames: {} ({})".format(
                num_frames,
                "texture: {}".format(texture_frames) if skip_first else "all in texture"
            ))
            self.info_size.setText("Texture Size: {} x {}".format(num_verts, texture_frames))
        else:
            self.info_verts.setText("Vertices: -")
            self.info_frames.setText("Frames: -")
            self.info_size.setText("Texture Size: -")

        self.validate_inputs()

    def validate_inputs(self):
        """Validate inputs and enable/disable encode button"""
        mesh_name = self.mesh_line.text()
        output_dir = self.output_line.text()
        skip_first = self.skip_first_check.isChecked()
        num_frames = self.frame_end.value() - self.frame_start.value() + 1

        # Skip first frame requires at least 2 frames
        min_frames = 2 if skip_first else 1

        valid = (
            mesh_name and
            cmds.objExists(mesh_name) and
            output_dir and
            num_frames >= min_frames
        )

        self.encode_btn.setEnabled(valid)

    def create_vat_uv(self):
        """Create VAT UV set on the mesh (independent operation)"""
        mesh_name = self.mesh_line.text()

        if not mesh_name:
            cmds.warning("Please select a mesh first")
            self.uv_status_label.setText("Status: No mesh selected")
            return

        if not cmds.objExists(mesh_name):
            cmds.warning("Mesh '{}' not found".format(mesh_name))
            self.uv_status_label.setText("Status: Mesh not found")
            return

        uv_set_name = self.uv_set_line.text().strip()
        if not uv_set_name:
            uv_set_name = "VAT_UV"
            self.uv_set_line.setText(uv_set_name)

        force = self.uv_force_check.isChecked()
        num_verts = utils.get_vertex_count(mesh_name)
        num_frames = self.frame_end.value() - self.frame_start.value() + 1

        try:
            result = utils.create_vat_uv(mesh_name, num_verts, num_frames, uv_set_name, force)

            if result.get('skipped'):
                self.uv_status_label.setText(
                    "Status: '{}' already exists (skipped)".format(uv_set_name)
                )
                QtWidgets.QMessageBox.warning(
                    self,
                    "Skipped",
                    "VAT UV '{}' already exists!\n\n"
                    "Check 'Overwrite if exists' to replace it.".format(uv_set_name)
                )
            else:
                self.uv_status_label.setText(
                    "Status: Created '{}' ({} verts)".format(uv_set_name, num_verts)
                )
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    "VAT UV '{}' created successfully!\n\n"
                    "Vertices: {}\n"
                    "Frames: {}\n\n"
                    "You can verify in UV Editor > UV Sets".format(
                        uv_set_name, num_verts, num_frames
                    )
                )
        except Exception as e:
            self.uv_status_label.setText("Status: Error")
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "Failed to create VAT UV:\n{}".format(str(e))
            )

    def encode_vat(self):
        """Execute VAT encoding"""
        mesh_name = self.mesh_line.text()
        output_dir = self.output_line.text()
        frame_start = self.frame_start.value()
        frame_end = self.frame_end.value()
        include_normals = self.normals_check.isChecked()
        export_mesh = self.export_mesh_check.isChecked()
        use_world_space = self.space_combo.currentData()
        uv_set_name = self.uv_set_line.text().strip() or "VAT_UV"
        force_uv = self.uv_force_check.isChecked()
        skip_first_frame = self.skip_first_check.isChecked()

        self.encode_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        try:
            result = core.encode_vat(
                mesh_name=mesh_name,
                output_dir=output_dir,
                frame_start=frame_start,
                frame_end=frame_end,
                include_normals=include_normals,
                export_mesh=export_mesh,
                use_world_space=use_world_space,
                uv_set_name=uv_set_name,
                force_uv=force_uv,
                skip_first_frame=skip_first_frame
            )

            if result["success"]:
                space_str = "World" if use_world_space else "Object (Local)"
                uv_status = "Created" if result.get("uv_created") else "Skipped (exists)"
                skip_str = "Yes (proxy only)" if skip_first_frame else "No"

                # Update UV status label
                if result.get("uv_skipped"):
                    self.uv_status_label.setText(
                        "Status: '{}' exists (skipped)".format(uv_set_name)
                    )
                else:
                    self.uv_status_label.setText(
                        "Status: '{}' created".format(uv_set_name)
                    )

                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    "VAT encoding complete!\n\n"
                    "Texture: {} x {}\n"
                    "Space: {}\n"
                    "Skip First Frame: {}\n"
                    "UV Set: {} ({})\n"
                    "Output: {}".format(
                        result["width"],
                        result["height"],
                        space_str,
                        skip_str,
                        uv_set_name,
                        uv_status,
                        result["png_path"]
                    )
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "VAT encoding failed:\n{}".format(str(e))
            )
        finally:
            self.progress_bar.setVisible(False)
            self.encode_btn.setEnabled(True)


def show():
    """Show OpenVAT window"""
    global _window

    if _window is not None:
        _window.close()
        _window.deleteLater()

    _window = OpenVATWindow()
    _window.show()

    return _window
