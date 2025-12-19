"""Main window for the Label Mender application."""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QListWidget, 
                             QSpinBox, QMessageBox, QSlider, QComboBox, 
                             QProgressBar, QGroupBox, QInputDialog, QApplication,
                             QSizePolicy)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QBrush, QIcon
from PyQt5.QtCore import Qt, QRect

from ..config import COLORS, STYLESHEET, DEFAULT_MODEL_PATH, VALID_IMAGE_EXTENSIONS, DEFAULT_CONFIDENCE, HANDLE_SIZE, VERSION
from ..config.styles import (PANEL_STYLE, CANVAS_STYLE, INFO_LABEL_STYLE, 
                             STATUS_SUCCESS_STYLE, STATUS_ERROR_STYLE, HINT_LABEL_STYLE)
from ..core import ModelManager, AnnotationManager, StateManager
from ..utils import BoxGeometry, FileManager
from .image_canvas import ImageCanvas


class MainWindow(QMainWindow):
    """Main application window for YOLO annotation tool."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Label Mender {VERSION}")
        self.setGeometry(50, 50, 1400, 900)
        self.setMinimumSize(1100, 700)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.icon_path = icon_path
        else:
            self.icon_path = None
        
        # Managers
        self.model_mgr = ModelManager()
        self.annotation_mgr = AnnotationManager()
        self.state_mgr = StateManager()
        self.file_mgr = FileManager()
        
        # State variables
        self.image_folder = ""
        self.image_list = []
        self.current_index = 0
        self.current_image_path = ""
        self.original_pixmap = None
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Class and threshold
        self.class_names = {}
        self.confidence_threshold = DEFAULT_CONFIDENCE
        self.raw_detections = []
        
        # Drawing mode
        self.draw_mode = False
        self.default_class = 0
        
        # Class file path
        self.class_file_path = ""
        
        self.init_ui()
        self.auto_load_model()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setStyleSheet(STYLESHEET)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Left Panel - Image Canvas
        canvas_wrapper = QWidget()
        canvas_wrapper.setStyleSheet(CANVAS_STYLE)
        canvas_layout = QVBoxLayout(canvas_wrapper)
        canvas_layout.setContentsMargins(4, 4, 4, 4)
        
        self.image_label = ImageCanvas(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"background-color: {COLORS['canvas']};")
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout.addWidget(self.image_label)
        
        # Right Panel - Controls
        right_panel = self.create_control_panel()
        
        main_layout.addWidget(canvas_wrapper, 80)
        main_layout.addWidget(right_panel, 20)
    
    def create_control_panel(self):
        """Create the right control panel."""
        right_panel = QWidget()
        right_panel.setStyleSheet(PANEL_STYLE)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_panel.setFixedWidth(280)
        
        # Header with logo and version
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        
        if self.icon_path:
            logo_label = QLabel()
            logo_pixmap = QPixmap(self.icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setFixedSize(36, 36)
            header_row.addWidget(logo_label)
        
        title_label = QLabel(f"Label Mender {VERSION}")
        title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 600;")
        header_row.addWidget(title_label)
        header_row.addStretch()
        
        right_layout.addLayout(header_row)
        
        # Configuration Section
        config_group = self.create_config_section()
        
        # Detections Section
        detect_group = self.create_detections_section()
        
        # Edit Section
        edit_group = self.create_edit_section()
        
        # Navigation Section
        nav_group = self.create_navigation_section()
        
        # Info label
        self.lbl_info = QLabel("Ready")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet(INFO_LABEL_STYLE)
        
        # Assemble right panel
        right_layout.addWidget(config_group)
        right_layout.addWidget(detect_group)
        right_layout.addWidget(edit_group)
        right_layout.addWidget(nav_group)
        right_layout.addWidget(self.lbl_info)
        right_layout.addStretch()
        
        return right_panel
    
    def create_config_section(self):
        """Create configuration group box."""
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(4)
        
        # Model/Classes row
        model_row = QHBoxLayout()
        self.btn_load_model = QPushButton("Load Model")
        self.btn_load_model.clicked.connect(self.load_model)
        self.btn_load_classes = QPushButton("Load Classes")
        self.btn_load_classes.clicked.connect(self.load_class_names)
        model_row.addWidget(self.btn_load_model)
        model_row.addWidget(self.btn_load_classes)
        config_layout.addLayout(model_row)
        
        self.lbl_model_status = QLabel("Model: Not loaded")
        self.lbl_model_status.setStyleSheet(STATUS_ERROR_STYLE)
        config_layout.addWidget(self.lbl_model_status)
        
        # Folder row
        folder_row = QHBoxLayout()
        self.btn_open_dir = QPushButton("Open Folder")
        self.btn_open_dir.clicked.connect(self.open_directory)
        self.btn_add_class = QPushButton("Add Class")
        self.btn_add_class.clicked.connect(self.add_new_class)
        folder_row.addWidget(self.btn_open_dir)
        folder_row.addWidget(self.btn_add_class)
        config_layout.addLayout(folder_row)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%v / %m  (%p%)")
        self.progress_bar.setTextVisible(True)
        config_layout.addWidget(self.progress_bar)
        
        # Confidence threshold
        conf_row = QHBoxLayout()
        conf_row.addWidget(QLabel("Conf:"))
        self.conf_slider = QSlider(Qt.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(int(DEFAULT_CONFIDENCE * 100))
        self.conf_slider.valueChanged.connect(self.on_confidence_changed)
        conf_row.addWidget(self.conf_slider)
        self.lbl_conf_value = QLabel(f"{DEFAULT_CONFIDENCE:.2f}")
        self.lbl_conf_value.setFixedWidth(32)
        self.lbl_conf_value.setStyleSheet(f"color: {COLORS['accent']};")
        conf_row.addWidget(self.lbl_conf_value)
        config_layout.addLayout(conf_row)
        
        return config_group
    
    def create_detections_section(self):
        """Create detections group box."""
        detect_group = QGroupBox("Detections")
        detect_layout = QVBoxLayout(detect_group)
        detect_layout.setSpacing(4)
        
        self.box_list = QListWidget()
        self.box_list.setMaximumHeight(120)
        self.box_list.currentRowChanged.connect(self.list_selection_changed)
        detect_layout.addWidget(self.box_list)
        
        self.btn_sort_boxes = QPushButton("Sort Left to Right")
        self.btn_sort_boxes.clicked.connect(self.sort_boxes_left_to_right)
        detect_layout.addWidget(self.btn_sort_boxes)
        
        return detect_group
    
    def create_edit_section(self):
        """Create edit group box."""
        edit_group = QGroupBox("Edit")
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setSpacing(4)
        
        # Draw mode
        self.btn_draw_mode = QPushButton("Draw Mode: OFF  [W]")
        self.btn_draw_mode.setCheckable(True)
        self.btn_draw_mode.clicked.connect(self.toggle_draw_mode)
        edit_layout.addWidget(self.btn_draw_mode)
        
        # Hint label
        self.lbl_edit_hint = QLabel("Click to select, drag to move/resize")
        self.lbl_edit_hint.setStyleSheet(HINT_LABEL_STYLE)
        edit_layout.addWidget(self.lbl_edit_hint)
        
        # Class selector
        class_row = QHBoxLayout()
        class_row.addWidget(QLabel("Class:"))
        self.combo_class = QComboBox()
        self.combo_class.currentIndexChanged.connect(self.update_current_box_class)
        class_row.addWidget(self.combo_class, 1)
        self.spin_class = QSpinBox()
        self.spin_class.setRange(0, 99)
        self.spin_class.valueChanged.connect(self.update_current_box_class_spin)
        self.spin_class.setVisible(False)
        class_row.addWidget(self.spin_class)
        edit_layout.addLayout(class_row)
        
        # New box class
        new_class_row = QHBoxLayout()
        new_class_row.addWidget(QLabel("New Box:"))
        self.spin_new_class = QSpinBox()
        self.spin_new_class.setRange(0, 99)
        self.spin_new_class.setValue(0)
        self.spin_new_class.valueChanged.connect(self.update_default_class)
        new_class_row.addWidget(self.spin_new_class)
        edit_layout.addLayout(new_class_row)
        
        # Delete box
        self.btn_delete_box = QPushButton("Delete Box  [Del]")
        self.btn_delete_box.clicked.connect(self.delete_current_box)
        edit_layout.addWidget(self.btn_delete_box)
        
        # Undo/Redo
        undo_row = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo = QPushButton("Redo")
        self.btn_redo.clicked.connect(self.redo)
        undo_row.addWidget(self.btn_undo)
        undo_row.addWidget(self.btn_redo)
        edit_layout.addLayout(undo_row)
        
        return edit_group
    
    def create_navigation_section(self):
        """Create navigation group box."""
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(4)
        
        # Prev/Next
        nav_btn_row = QHBoxLayout()
        self.btn_prev = QPushButton("Prev [A]")
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next = QPushButton("Next [D]")
        self.btn_next.clicked.connect(self.next_image)
        nav_btn_row.addWidget(self.btn_prev)
        nav_btn_row.addWidget(self.btn_next)
        nav_layout.addLayout(nav_btn_row)
        
        # Save button
        self.btn_save = QPushButton("SAVE  [S]")
        self.btn_save.setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.save_annotation)
        nav_layout.addWidget(self.btn_save)
        
        # Skip & Delete
        action_row = QHBoxLayout()
        self.btn_skip = QPushButton("Skip [Q]")
        self.btn_skip.clicked.connect(self.skip_image)
        self.btn_delete_image = QPushButton("Delete [X]")
        self.btn_delete_image.clicked.connect(self.delete_current_image)
        action_row.addWidget(self.btn_skip)
        action_row.addWidget(self.btn_delete_image)
        nav_layout.addLayout(action_row)
        
        # Next Unannotated
        self.btn_next_unannotated = QPushButton("Next Unannotated [N]")
        self.btn_next_unannotated.clicked.connect(self.goto_next_unannotated)
        nav_layout.addWidget(self.btn_next_unannotated)
        
        return nav_group
    
    # ==================== MODEL & CLASS LOADING ====================
    
    def load_model(self):
        """Load YOLO model from file dialog."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Model", "", "PyTorch Model (*.pt)")
        if path:
            self._load_model_from_path(path)
    
    def auto_load_model(self):
        """Automatically load default model if it exists."""
        if os.path.exists(DEFAULT_MODEL_PATH):
            self._load_model_from_path(DEFAULT_MODEL_PATH)
    
    def _load_model_from_path(self, path):
        """Internal method to load model from path."""
        if self.model_mgr.load_model(path):
            self.lbl_model_status.setText(f"Model: {self.model_mgr.get_model_name()}")
            self.lbl_model_status.setStyleSheet(STATUS_SUCCESS_STYLE)
            
            # Load class names from model
            model_classes = self.model_mgr.get_class_names()
            if model_classes:
                self.class_names = model_classes
                self.update_class_combo()
        else:
            QMessageBox.critical(self, "Error", "Failed to load model")
    
    def load_class_names(self):
        """Load class names from file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Class File", "", 
            "YAML Files (*.yaml *.yml);;Text Files (*.txt);;All Files (*)"
        )
        if path:
            try:
                self.class_names = self.file_mgr.load_class_names(path)
                self.class_file_path = path
                self.update_class_combo()
                self.update_list_widget()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load classes: {str(e)}")
    
    def add_new_class(self):
        """Add a new class through dialog."""
        name, ok = QInputDialog.getText(self, "Add New Class", "Enter class name:")
        if ok and name.strip():
            name = name.strip()
            new_id = max(self.class_names.keys()) + 1 if self.class_names else 0
            self.class_names[new_id] = name
            self.update_class_combo()
            self.save_classes_to_file()
            QMessageBox.information(self, "Success", f"Added class {new_id}: {name}")
    
    def save_classes_to_file(self):
        """Save class names to file."""
        if not self.class_file_path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Classes", "", 
                "Text Files (*.txt);;YAML Files (*.yaml)"
            )
            if path:
                self.class_file_path = path
            else:
                return
        
        try:
            self.file_mgr.save_class_names(self.class_file_path, self.class_names)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save classes: {str(e)}")
    
    def update_class_combo(self):
        """Update class combo box with current classes."""
        self.combo_class.blockSignals(True)
        self.combo_class.clear()
        
        if self.class_names:
            self.combo_class.setVisible(True)
            self.spin_class.setVisible(False)
            for idx in sorted(self.class_names.keys()):
                self.combo_class.addItem(f"{idx}: {self.class_names[idx]}", idx)
        else:
            self.combo_class.setVisible(False)
            self.spin_class.setVisible(True)
        
        self.combo_class.blockSignals(False)
    
    def get_class_name(self, class_id):
        """Get class name for ID."""
        return self.class_names.get(class_id, f"Class {class_id}")
    
    # ==================== FOLDER & IMAGE LOADING ====================
    
    def open_directory(self):
        """Open directory and load image list."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if dir_path:
            self.image_folder = dir_path
            self.image_list = self.file_mgr.get_image_list(dir_path, VALID_IMAGE_EXTENSIONS)
            
            if not self.image_list:
                QMessageBox.warning(self, "Warning", "No images found in folder")
                return
            
            self.progress_bar.setMaximum(len(self.image_list))
            self.update_progress()
            
            first_unannotated = self.find_first_unannotated()
            self.current_index = first_unannotated if first_unannotated >= 0 else 0
            self.load_image()
    
    def update_progress(self):
        """Update progress bar."""
        if not self.image_list:
            return
        annotated = sum(
            1 for img in self.image_list 
            if self.file_mgr.annotation_exists(self.image_folder, img)
        )
        self.progress_bar.setValue(annotated)
    
    def load_image(self):
        """Load current image and annotations."""
        if not self.image_list:
            return
        
        filename = self.image_list[self.current_index]
        self.current_image_path = os.path.join(self.image_folder, filename)
        self.original_pixmap = QPixmap(self.current_image_path)
        self.display_image()
        
        self.lbl_info.setText(f"{filename}  ({self.current_index + 1}/{len(self.image_list)})")
        self.state_mgr.clear()
        
        txt_path = os.path.splitext(self.current_image_path)[0] + ".txt"
        self.annotation_mgr.clear()
        self.raw_detections = []
        
        if os.path.exists(txt_path):
            boxes = self.file_mgr.load_annotations(txt_path)
            self.annotation_mgr.set_boxes(boxes)
        elif self.model_mgr.is_loaded():
            self.run_inference()
        
        self.update_list_widget()
        self.draw_boxes()
    
    def run_inference(self):
        """Run model inference on current image."""
        self.raw_detections = self.model_mgr.run_inference(
            self.current_image_path, 
            self.confidence_threshold
        )
        self.apply_confidence_filter()
    
    def apply_confidence_filter(self):
        """Apply confidence threshold filter."""
        filtered = self.annotation_mgr.filter_by_confidence(
            self.raw_detections, 
            self.confidence_threshold
        )
        self.annotation_mgr.set_boxes(filtered)
        self.update_list_widget()
        self.draw_boxes()
    
    def on_confidence_changed(self, value):
        """Handle confidence slider change."""
        self.confidence_threshold = value / 100.0
        self.lbl_conf_value.setText(f"{self.confidence_threshold:.2f}")
        if self.raw_detections:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.apply_confidence_filter()
    
    # ==================== DISPLAY ====================
    
    def display_image(self):
        """Display image on canvas."""
        if self.original_pixmap:
            scaled = self.original_pixmap.scaled(
                self.image_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.scale_factor_x = scaled.width() / self.original_pixmap.width()
            self.scale_factor_y = scaled.height() / self.original_pixmap.height()
            self.offset_x = (self.image_label.width() - scaled.width()) / 2
            self.offset_y = (self.image_label.height() - scaled.height()) / 2
    
    def draw_boxes(self):
        """Draw all boxes on image."""
        if not self.original_pixmap:
            return
        
        scaled = self.original_pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        canvas = scaled.copy()
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        boxes = self.annotation_mgr.get_boxes()
        selected_idx = self.annotation_mgr.selected_index
        
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(
                box, orig_w, orig_h, 
                self.scale_factor_x, self.scale_factor_y
            )
            
            if not rect:
                continue
            
            is_selected = (i == selected_idx)
            
            # Draw box
            if is_selected:
                pen = QPen(QColor(0, 200, 255), 2)
            else:
                pen = QPen(QColor(255, 80, 80), 2)
            
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            
            # Draw resize handles for selected box
            if is_selected:
                self.draw_handles(painter, rect)
            
            # Label
            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            label = f"{self.get_class_name(box['class'])} {box.get('conf', 1.0):.2f}"
            
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.fillRect(
                int(rect.x()), int(rect.y()) - text_rect.height() - 2,
                text_rect.width() + 6, text_rect.height() + 2, 
                QColor(0, 0, 0, 180)
            )
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(rect.x()) + 3, int(rect.y()) - 4, label)
        
        # Plate reading overlay
        plate_text = self.annotation_mgr.get_plate_reading(self.class_names)
        if plate_text:
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            text_rect = painter.fontMetrics().boundingRect(plate_text)
            bg_x = (canvas.width() - text_rect.width() - 24) // 2
            bg_y = canvas.height() - 38
            painter.fillRect(bg_x, bg_y, text_rect.width() + 24, 32, QColor(0, 0, 0, 220))
            painter.setPen(QColor(100, 255, 150))
            painter.drawText(bg_x + 12, bg_y + 23, plate_text)
        
        painter.end()
        self.image_label.setPixmap(canvas)
    
    def draw_handles(self, painter, rect):
        """Draw resize handles on the selected box."""
        hs = HANDLE_SIZE
        handle_color = QColor(255, 255, 255)
        handle_border = QColor(0, 150, 200)
        
        painter.setBrush(QBrush(handle_color))
        painter.setPen(QPen(handle_border, 1))
        
        # Corner handles
        corners = [
            (rect.left() - hs//2, rect.top() - hs//2),
            (rect.right() - hs//2, rect.top() - hs//2),
            (rect.left() - hs//2, rect.bottom() - hs//2),
            (rect.right() - hs//2, rect.bottom() - hs//2),
        ]
        
        for cx, cy in corners:
            painter.drawRect(cx, cy, hs, hs)
        
        # Edge handles (midpoints)
        edges = [
            (rect.center().x() - hs//2, rect.top() - hs//2),
            (rect.center().x() - hs//2, rect.bottom() - hs//2),
            (rect.left() - hs//2, rect.center().y() - hs//2),
            (rect.right() - hs//2, rect.center().y() - hs//2),
        ]
        
        for ex, ey in edges:
            painter.drawRect(ex, ey, hs, hs)
    
    # ==================== DRAWING MODE ====================
    
    def toggle_draw_mode(self):
        """Toggle drawing mode on/off."""
        self.draw_mode = not self.draw_mode
        if self.draw_mode:
            self.btn_draw_mode.setText("Draw Mode: ON  [W]")
            self.btn_draw_mode.setChecked(True)
            self.image_label.setCursor(Qt.CrossCursor)
        else:
            self.btn_draw_mode.setText("Draw Mode: OFF  [W]")
            self.btn_draw_mode.setChecked(False)
            self.image_label.setCursor(Qt.ArrowCursor)
    
    def update_default_class(self, value):
        """Update default class for new boxes."""
        self.default_class = value
    
    def draw_temp_box(self, start, end):
        """Draw temporary box while dragging."""
        if not self.original_pixmap:
            return
        
        scaled = self.original_pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        canvas = scaled.copy()
        painter = QPainter(canvas)
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        
        # Draw existing boxes
        boxes = self.annotation_mgr.get_boxes()
        selected_idx = self.annotation_mgr.selected_index
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(
                box, orig_w, orig_h, 
                self.scale_factor_x, self.scale_factor_y
            )
            if rect:
                pen = QPen(QColor(0, 200, 255), 2) if i == selected_idx else QPen(QColor(255, 80, 80), 2)
                painter.setPen(pen)
                painter.drawRect(rect)
        
        # Draw temp box
        pen = QPen(QColor(0, 180, 255), 2, Qt.DashLine)
        painter.setPen(pen)
        
        x1, y1 = start.x() - self.offset_x, start.y() - self.offset_y
        x2, y2 = end.x() - self.offset_x, end.y() - self.offset_y
        
        rect = QRect(int(min(x1, x2)), int(min(y1, y2)), int(abs(x2 - x1)), int(abs(y2 - y1)))
        painter.drawRect(rect)
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(
            int(min(x1, x2)), int(min(y1, y2)) - 4, 
            f"New: {self.get_class_name(self.default_class)}"
        )
        
        painter.end()
        self.image_label.setPixmap(canvas)
    
    def finalize_new_box(self, start, end):
        """Finalize newly drawn box."""
        if not self.original_pixmap:
            return
        
        x1, y1 = start.x() - self.offset_x, start.y() - self.offset_y
        x2, y2 = end.x() - self.offset_x, end.y() - self.offset_y
        
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.draw_boxes()
            return
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        
        px_x1, px_y1 = min(x1, x2) / self.scale_factor_x, min(y1, y2) / self.scale_factor_y
        px_x2, px_y2 = max(x1, x2) / self.scale_factor_x, max(y1, y2) / self.scale_factor_y
        
        box_coords = BoxGeometry.normalize_box_coords(
            px_x1, px_y1, px_x2, px_y2, orig_w, orig_h
        )
        
        self.state_mgr.save_state(self.annotation_mgr.get_boxes())
        new_box = {
            'class': self.default_class,
            'conf': 1.0,
            **box_coords
        }
        idx = self.annotation_mgr.add_box(new_box)
        self.update_list_widget()
        self.draw_boxes()
        
        self.annotation_mgr.select_box(idx)
        self.box_list.setCurrentRow(idx)
    
    # ==================== BOX SELECTION & EDITING ====================
    
    def select_box_at(self, mouse_x, mouse_y):
        """Select box at mouse position."""
        if not self.original_pixmap:
            return
        
        real_x, real_y = mouse_x - self.offset_x, mouse_y - self.offset_y
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        
        selected_idx = -1
        boxes = self.annotation_mgr.get_boxes()
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(
                box, orig_w, orig_h, 
                self.scale_factor_x, self.scale_factor_y
            )
            if rect and rect.contains(int(real_x), int(real_y)):
                selected_idx = i
        
        self.annotation_mgr.select_box(selected_idx)
        if selected_idx != -1:
            self.box_list.setCurrentRow(selected_idx)
            self.update_class_selector(boxes[selected_idx]['class'])
        self.draw_boxes()
    
    def update_list_widget(self):
        """Update the box list widget."""
        self.box_list.clear()
        boxes = self.annotation_mgr.get_boxes()
        sorted_indices = self.annotation_mgr.get_sorted_indices()
        
        for pos, i in enumerate(sorted_indices):
            box = boxes[i]
            self.box_list.addItem(
                f"{pos+1}. {self.get_class_name(box['class'])}  ({box.get('conf', 1.0):.2f})"
            )
    
    def list_selection_changed(self, row):
        """Handle list selection change."""
        boxes = self.annotation_mgr.get_boxes()
        if 0 <= row < len(boxes):
            self.annotation_mgr.select_box(row)
            self.update_class_selector(boxes[row]['class'])
            self.draw_boxes()
    
    def update_class_selector(self, class_id):
        """Update class selector to show current class."""
        if self.class_names:
            for i in range(self.combo_class.count()):
                if self.combo_class.itemData(i) == class_id:
                    self.combo_class.blockSignals(True)
                    self.combo_class.setCurrentIndex(i)
                    self.combo_class.blockSignals(False)
                    break
        else:
            self.spin_class.blockSignals(True)
            self.spin_class.setValue(class_id)
            self.spin_class.blockSignals(False)
    
    def update_current_box_class(self, index):
        """Update class of currently selected box (from combo)."""
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0 and self.class_names:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            new_class = self.combo_class.itemData(index)
            self.annotation_mgr.update_box_class(selected_idx, new_class)
            self.update_list_widget()
            self.box_list.setCurrentRow(selected_idx)
            self.draw_boxes()
    
    def update_current_box_class_spin(self):
        """Update class of currently selected box (from spinbox)."""
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0 and not self.class_names:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.annotation_mgr.update_box_class(selected_idx, self.spin_class.value())
            self.update_list_widget()
            self.box_list.setCurrentRow(selected_idx)
            self.draw_boxes()
    
    def delete_current_box(self):
        """Delete currently selected box."""
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.annotation_mgr.delete_box(selected_idx)
            self.update_list_widget()
            self.draw_boxes()
    
    def sort_boxes_left_to_right(self):
        """Sort boxes by x coordinate."""
        boxes = self.annotation_mgr.get_boxes()
        if not boxes:
            return
        self.state_mgr.save_state(boxes)
        self.annotation_mgr.sort_boxes_by_x()
        self.update_list_widget()
        self.draw_boxes()
    
    # ==================== UNDO / REDO ====================
    
    def undo(self):
        """Undo last operation."""
        boxes = self.annotation_mgr.get_boxes()
        prev_state = self.state_mgr.undo(boxes)
        if prev_state is not None:
            self.annotation_mgr.set_boxes(prev_state)
            self.update_list_widget()
            self.draw_boxes()
    
    def redo(self):
        """Redo last undone operation."""
        boxes = self.annotation_mgr.get_boxes()
        next_state = self.state_mgr.redo(boxes)
        if next_state is not None:
            self.annotation_mgr.set_boxes(next_state)
            self.update_list_widget()
            self.draw_boxes()
    
    # ==================== SAVE ====================
    
    def save_annotation(self, go_next=True):
        """Save current annotations."""
        if not self.current_image_path:
            return
        
        txt_path = os.path.splitext(self.current_image_path)[0] + ".txt"
        boxes = self.annotation_mgr.get_boxes()
        self.file_mgr.save_annotations(txt_path, boxes)
        
        self.lbl_info.setText("Saved")
        self.update_progress()
        QApplication.processEvents()
        
        if go_next and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    # ==================== NAVIGATION ====================
    
    def next_image(self):
        """Go to next image."""
        self.save_annotation(go_next=False)
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    def prev_image(self):
        """Go to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def skip_image(self):
        """Skip to next image without saving."""
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    def find_first_unannotated(self):
        """Find first unannotated image."""
        for i, img in enumerate(self.image_list):
            if not self.file_mgr.annotation_exists(self.image_folder, img):
                return i
        return -1
    
    def find_next_unannotated(self, start_from=None):
        """Find next unannotated image."""
        start = start_from if start_from is not None else self.current_index + 1
        
        for i in range(start, len(self.image_list)):
            if not self.file_mgr.annotation_exists(self.image_folder, self.image_list[i]):
                return i
        for i in range(0, start):
            if not self.file_mgr.annotation_exists(self.image_folder, self.image_list[i]):
                return i
        return -1
    
    def goto_next_unannotated(self):
        """Go to next unannotated image."""
        if not self.image_list:
            return
        next_idx = self.find_next_unannotated()
        if next_idx >= 0:
            self.current_index = next_idx
            self.load_image()
        else:
            QMessageBox.information(self, "Complete", "All images have been annotated.")
    
    def delete_current_image(self):
        """Delete current image and annotation."""
        if not self.current_image_path or not self.image_list:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {os.path.basename(self.current_image_path)}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                img_path = self.current_image_path
                txt_path = os.path.splitext(img_path)[0] + ".txt"
                filename = os.path.basename(img_path)
                
                if os.path.exists(img_path):
                    os.remove(img_path)
                if os.path.exists(txt_path):
                    os.remove(txt_path)
                
                self.image_list.remove(filename)
                
                if not self.image_list:
                    self.current_image_path = ""
                    self.annotation_mgr.clear()
                    self.image_label.setText("No images")
                    return
                
                if self.current_index >= len(self.image_list):
                    self.current_index = len(self.image_list) - 1
                
                self.progress_bar.setMaximum(len(self.image_list))
                self.update_progress()
                self.load_image()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    # ==================== KEYBOARD SHORTCUTS ====================
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.undo()
                return
            elif event.key() == Qt.Key_Y:
                self.redo()
                return
            elif event.key() == Qt.Key_S:
                self.save_annotation()
                return
        
        key = event.key()
        if key == Qt.Key_D:
            self.next_image()
        elif key == Qt.Key_A:
            self.prev_image()
        elif key == Qt.Key_S:
            self.save_annotation()
        elif key == Qt.Key_W:
            self.toggle_draw_mode()
        elif key == Qt.Key_Q:
            self.skip_image()
        elif key == Qt.Key_N:
            self.goto_next_unannotated()
        elif key == Qt.Key_X:
            self.delete_current_image()
        elif key == Qt.Key_Escape:
            if self.draw_mode:
                self.toggle_draw_mode()
            else:
                self.annotation_mgr.deselect()
                self.draw_boxes()
        elif key == Qt.Key_Delete:
            self.delete_current_box()
        elif Qt.Key_1 <= key <= Qt.Key_9:
            selected_idx = self.annotation_mgr.selected_index
            if selected_idx >= 0:
                self.state_mgr.save_state(self.annotation_mgr.get_boxes())
                new_class = key - Qt.Key_1
                self.annotation_mgr.update_box_class(selected_idx, new_class)
                self.update_class_selector(new_class)
                self.update_list_widget()
                self.box_list.setCurrentRow(selected_idx)
                self.draw_boxes()
        elif key == Qt.Key_0:
            selected_idx = self.annotation_mgr.selected_index
            if selected_idx >= 0:
                self.state_mgr.save_state(self.annotation_mgr.get_boxes())
                self.annotation_mgr.update_box_class(selected_idx, 9)
                self.update_class_selector(9)
                self.update_list_widget()
                self.box_list.setCurrentRow(selected_idx)
                self.draw_boxes()
