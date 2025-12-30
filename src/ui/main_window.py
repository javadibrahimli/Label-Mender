"""Main window for the Label Mender application."""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QListWidget, 
                             QSpinBox, QMessageBox, QSlider, QComboBox, 
                             QProgressBar, QGroupBox, QInputDialog, QApplication,
                             QSizePolicy, QTabWidget, QScrollArea, QFrame)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QBrush, QIcon
from PyQt5.QtCore import Qt, QRect

from ..config import COLORS, STYLESHEET, DEFAULT_MODEL_PATH, VALID_IMAGE_EXTENSIONS, DEFAULT_CONFIDENCE, HANDLE_SIZE, VERSION
from ..config.styles import (PANEL_STYLE, CANVAS_STYLE, INFO_LABEL_STYLE, 
                             STATUS_SUCCESS_STYLE, STATUS_ERROR_STYLE, HINT_LABEL_STYLE)
from ..core import ModelManager, AnnotationManager, StateManager
from ..utils import BoxGeometry, FileManager
from .image_canvas import ImageCanvas


class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Label Mender {VERSION}")
        self.setGeometry(50, 50, 1400, 900)
        self.setMinimumSize(1100, 700)
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.icon_path = icon_path
        else:
            self.icon_path = None
        
        self.model_mgr = ModelManager()
        self.annotation_mgr = AnnotationManager()
        self.state_mgr = StateManager()
        self.file_mgr = FileManager()
        
        self.image_folder = ""
        self.image_list = []
        self.current_index = 0
        self.current_image_path = ""
        self.original_pixmap = None
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        self.class_names = {}
        self.confidence_threshold = DEFAULT_CONFIDENCE
        self.raw_detections = []
        
        self.draw_mode = False
        self.default_class = 0
        
        self.mask_mode = False
        self.mask_rectangles = []
        self.selected_mask_index = -1
        
        self.class_file_path = ""
        
        self.init_ui()
        self.auto_load_model()
    
    def init_ui(self):
        self.setStyleSheet(STYLESHEET)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
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
        
        zoom_bar = QHBoxLayout()
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
        self.btn_reset_view = QPushButton("Reset [R]")
        self.btn_reset_view.setToolTip("Reset zoom and pan")
        self.btn_reset_view.setMaximumWidth(80)
        self.btn_reset_view.clicked.connect(self.reset_view)
        zoom_bar.addWidget(self.lbl_zoom)
        zoom_bar.addStretch()
        zoom_bar.addWidget(self.btn_reset_view)
        canvas_layout.addLayout(zoom_bar)
        
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(200)
        self.tabs.setMaximumWidth(350)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; background: {COLORS['panel']}; }}
            QTabBar::tab {{ background: {COLORS['surface']}; color: {COLORS['text']}; padding: 5px 10px; border: 1px solid {COLORS['border']}; font-size: 10px; }}
            QTabBar::tab:selected {{ background: {COLORS['accent']}; color: white; }}
        """)
        
        controls_tab = self.create_control_panel()
        stats_tab = self.create_stats_panel()
        
        self.tabs.addTab(controls_tab, "Controls")
        self.tabs.addTab(stats_tab, "Statistics")
        
        main_layout.addWidget(canvas_wrapper, 80)
        main_layout.addWidget(self.tabs, 20)
    
    def create_control_panel(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        right_panel = QWidget()
        right_panel.setStyleSheet(PANEL_STYLE)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_panel.setMinimumWidth(200)
        right_panel.setMaximumWidth(320)
        
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
        
        config_group = self.create_config_section()
        detect_group = self.create_detections_section()
        edit_group = self.create_edit_section()
        mask_group = self.create_mask_section()
        nav_group = self.create_navigation_section()
        
        self.lbl_info = QLabel("Ready")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet(INFO_LABEL_STYLE)
        
        right_layout.addWidget(config_group)
        right_layout.addWidget(detect_group)
        right_layout.addWidget(edit_group)
        right_layout.addWidget(mask_group)
        right_layout.addWidget(nav_group)
        right_layout.addWidget(self.lbl_info)
        right_layout.addStretch()
        
        scroll_area.setWidget(right_panel)
        return scroll_area
    
    def create_config_section(self):
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(4)
        
        model_row = QHBoxLayout()
        self.btn_load_model = QPushButton("Load .pt")
        self.btn_load_model.setToolTip("Load Ultralytics YOLO model (.pt)")
        self.btn_load_model.clicked.connect(self.load_model)
        self.btn_load_yolov4 = QPushButton("Load YOLOv4")
        self.btn_load_yolov4.setToolTip("Load YOLOv4-tiny model (.cfg + .weights + .names)")
        self.btn_load_yolov4.clicked.connect(self.load_yolov4_model)
        model_row.addWidget(self.btn_load_model)
        model_row.addWidget(self.btn_load_yolov4)
        config_layout.addLayout(model_row)
        
        classes_row = QHBoxLayout()
        self.btn_load_classes = QPushButton("Load Classes")
        self.btn_load_classes.clicked.connect(self.load_class_names)
        classes_row.addWidget(self.btn_load_classes)
        config_layout.addLayout(classes_row)
        
        self.lbl_model_status = QLabel("Model: Not loaded")
        self.lbl_model_status.setStyleSheet(STATUS_ERROR_STYLE)
        config_layout.addWidget(self.lbl_model_status)
        
        folder_row = QHBoxLayout()
        self.btn_open_dir = QPushButton("Open Folder")
        self.btn_open_dir.clicked.connect(self.open_directory)
        self.btn_add_class = QPushButton("Add Class")
        self.btn_add_class.clicked.connect(self.add_new_class)
        folder_row.addWidget(self.btn_open_dir)
        folder_row.addWidget(self.btn_add_class)
        config_layout.addLayout(folder_row)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%v / %m  (%p%)")
        self.progress_bar.setTextVisible(True)
        config_layout.addWidget(self.progress_bar)
        
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
        detect_group = QGroupBox("Detections")
        detect_layout = QVBoxLayout(detect_group)
        detect_layout.setSpacing(4)
        
        self.box_list = QListWidget()
        self.box_list.setMaximumHeight(120)
        self.box_list.currentRowChanged.connect(self.list_selection_changed)
        detect_layout.addWidget(self.box_list)
        
        self.btn_sort_boxes = QPushButton("Sort L→R")
        self.btn_sort_boxes.setToolTip("Sort boxes from left to right")
        self.btn_sort_boxes.clicked.connect(self.sort_boxes_left_to_right)
        detect_layout.addWidget(self.btn_sort_boxes)
        
        return detect_group
    
    def create_edit_section(self):
        edit_group = QGroupBox("Edit")
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setSpacing(4)
        
        self.btn_draw_mode = QPushButton("Draw: OFF [W]")
        self.btn_draw_mode.setCheckable(True)
        self.btn_draw_mode.setToolTip("Toggle draw mode to add new boxes")
        self.btn_draw_mode.clicked.connect(self.toggle_draw_mode)
        edit_layout.addWidget(self.btn_draw_mode)
        
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
        
        new_class_row = QHBoxLayout()
        new_class_row.addWidget(QLabel("New Box:"))
        self.spin_new_class = QSpinBox()
        self.spin_new_class.setRange(0, 99)
        self.spin_new_class.setValue(0)
        self.spin_new_class.valueChanged.connect(self.update_default_class)
        new_class_row.addWidget(self.spin_new_class)
        edit_layout.addLayout(new_class_row)
        
        self.btn_delete_box = QPushButton("Delete [Del]")
        self.btn_delete_box.setToolTip("Delete selected box")
        self.btn_delete_box.clicked.connect(self.delete_current_box)
        edit_layout.addWidget(self.btn_delete_box)
        
        undo_row = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo = QPushButton("Redo")
        self.btn_redo.clicked.connect(self.redo)
        undo_row.addWidget(self.btn_undo)
        undo_row.addWidget(self.btn_redo)
        edit_layout.addLayout(undo_row)
        
        return edit_group
    
    def create_mask_section(self):
        mask_group = QGroupBox("Mask (Hide Objects)")
        mask_layout = QVBoxLayout(mask_group)
        mask_layout.setSpacing(4)
        
        self.btn_mask_mode = QPushButton("Mask: OFF [M]")
        self.btn_mask_mode.setCheckable(True)
        self.btn_mask_mode.setToolTip("Draw gray rectangles to hide objects from training")
        self.btn_mask_mode.setStyleSheet(f"background-color: #555; color: white;")
        self.btn_mask_mode.clicked.connect(self.toggle_mask_mode)
        mask_layout.addWidget(self.btn_mask_mode)
        
        self.mask_list = QListWidget()
        self.mask_list.setMaximumHeight(80)
        self.mask_list.currentRowChanged.connect(self.mask_list_selection_changed)
        mask_layout.addWidget(self.mask_list)
        
        mask_btn_row = QHBoxLayout()
        self.btn_delete_mask = QPushButton("Delete")
        self.btn_delete_mask.setToolTip("Delete selected mask")
        self.btn_delete_mask.clicked.connect(self.delete_selected_mask)
        self.btn_clear_masks = QPushButton("Clear All")
        self.btn_clear_masks.setToolTip("Clear all masks")
        self.btn_clear_masks.clicked.connect(self.clear_all_masks)
        mask_btn_row.addWidget(self.btn_delete_mask)
        mask_btn_row.addWidget(self.btn_clear_masks)
        mask_layout.addLayout(mask_btn_row)
        
        return mask_group
    
    def create_navigation_section(self):
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(4)
        
        nav_btn_row = QHBoxLayout()
        self.btn_prev = QPushButton("← [A]")
        self.btn_prev.setToolTip("Previous image")
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next = QPushButton("[D] →")
        self.btn_next.setToolTip("Next image")
        self.btn_next.clicked.connect(self.next_image)
        nav_btn_row.addWidget(self.btn_prev)
        nav_btn_row.addWidget(self.btn_next)
        nav_layout.addLayout(nav_btn_row)
        
        self.btn_save = QPushButton("SAVE [S]")
        self.btn_save.setStyleSheet(f"background-color: {COLORS['accent']}; color: white; font-weight: bold; padding: 6px;")
        self.btn_save.clicked.connect(self.save_annotation)
        nav_layout.addWidget(self.btn_save)
        
        action_row = QHBoxLayout()
        self.btn_skip = QPushButton("Skip [Q]")
        self.btn_skip.setToolTip("Skip to next image without saving")
        self.btn_skip.clicked.connect(self.skip_image)
        self.btn_delete_image = QPushButton("Del [X]")
        self.btn_delete_image.setToolTip("Delete current image")
        self.btn_delete_image.clicked.connect(self.delete_current_image)
        action_row.addWidget(self.btn_skip)
        action_row.addWidget(self.btn_delete_image)
        nav_layout.addLayout(action_row)
        
        self.btn_next_unannotated = QPushButton("Next Empty [N]")
        self.btn_next_unannotated.setToolTip("Jump to next unannotated image")
        self.btn_next_unannotated.clicked.connect(self.goto_next_unannotated)
        nav_layout.addWidget(self.btn_next_unannotated)
        
        return nav_group
    
    def create_stats_panel(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        stats_widget = QWidget()
        stats_widget.setStyleSheet(PANEL_STYLE)
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(6)
        stats_layout.setContentsMargins(6, 6, 6, 6)
        stats_widget.setMinimumWidth(200)
        stats_widget.setMaximumWidth(320)
        
        self.btn_refresh_stats = QPushButton("Refresh Stats")
        self.btn_refresh_stats.setToolTip("Scan folder and update statistics")
        self.btn_refresh_stats.clicked.connect(self.update_statistics)
        stats_layout.addWidget(self.btn_refresh_stats)
        
        overview_group = QGroupBox("Overview")
        overview_layout = QVBoxLayout(overview_group)
        overview_layout.setSpacing(2)
        
        self.lbl_total_images = QLabel("Images: 0")
        self.lbl_annotated_images = QLabel("Annotated: 0")
        self.lbl_unannotated_images = QLabel("Empty: 0")
        self.lbl_total_boxes = QLabel("Boxes: 0")
        self.lbl_avg_boxes = QLabel("Avg/Image: 0.0")
        
        for lbl in [self.lbl_total_images, self.lbl_annotated_images, 
                    self.lbl_unannotated_images, self.lbl_total_boxes, self.lbl_avg_boxes]:
            lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px; padding: 1px;")
            overview_layout.addWidget(lbl)
        
        stats_layout.addWidget(overview_group)
        
        class_group = QGroupBox("Classes")
        class_layout = QVBoxLayout(class_group)
        
        self.class_stats_list = QListWidget()
        self.class_stats_list.setMinimumHeight(100)
        self.class_stats_list.setStyleSheet(f"""
            QListWidget {{ background: {COLORS['surface']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; font-size: 9px; }}
            QListWidget::item {{ padding: 2px; }}
        """)
        class_layout.addWidget(self.class_stats_list)
        
        stats_layout.addWidget(class_group)
        
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.stats_progress_bar = QProgressBar()
        self.stats_progress_bar.setFormat("%v/%m (%p%)")
        self.stats_progress_bar.setTextVisible(True)
        self.stats_progress_bar.setStyleSheet(f"""
            QProgressBar {{ border: 1px solid {COLORS['border']}; background: {COLORS['surface']}; text-align: center; color: {COLORS['text']}; font-size: 9px; }}
            QProgressBar::chunk {{ background: {COLORS['accent']}; }}
        """)
        progress_layout.addWidget(self.stats_progress_bar)
        
        stats_layout.addWidget(progress_group)
        stats_layout.addStretch()
        
        scroll_area.setWidget(stats_widget)
        return scroll_area
    
    def update_statistics(self):
        if not self.image_folder or not self.image_list:
            self.lbl_total_images.setText("Images: 0")
            self.lbl_annotated_images.setText("Annotated: 0")
            self.lbl_unannotated_images.setText("Empty: 0")
            self.lbl_total_boxes.setText("Boxes: 0")
            self.lbl_avg_boxes.setText("Avg/Image: 0.0")
            self.class_stats_list.clear()
            self.stats_progress_bar.setMaximum(1)
            self.stats_progress_bar.setValue(0)
            return
        
        total_images = len(self.image_list)
        annotated = 0
        total_boxes = 0
        class_counts = {}
        
        for img in self.image_list:
            txt_path = os.path.join(self.image_folder, os.path.splitext(img)[0] + ".txt")
            if os.path.exists(txt_path):
                annotated += 1
                boxes = self.file_mgr.load_annotations(txt_path)
                total_boxes += len(boxes)
                for box in boxes:
                    cls = box['class']
                    class_name = self.class_names.get(cls, f"C{cls}")
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        unannotated = total_images - annotated
        avg_boxes = total_boxes / annotated if annotated > 0 else 0
        
        self.lbl_total_images.setText(f"Images: {total_images}")
        self.lbl_annotated_images.setText(f"Annotated: {annotated}")
        self.lbl_unannotated_images.setText(f"Empty: {unannotated}")
        self.lbl_total_boxes.setText(f"Boxes: {total_boxes}")
        self.lbl_avg_boxes.setText(f"Avg/Image: {avg_boxes:.1f}")
        
        self.class_stats_list.clear()
        sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
        for class_name, count in sorted_classes:
            percentage = (count / total_boxes * 100) if total_boxes > 0 else 0
            bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
            self.class_stats_list.addItem(f"{class_name}: {count} ({percentage:.0f}%) {bar}")
        
        self.stats_progress_bar.setMaximum(total_images)
        self.stats_progress_bar.setValue(annotated)
    
    def update_zoom_label(self):
        zoom_percent = int(self.image_label.zoom_level * 100)
        self.lbl_zoom.setText(f"{zoom_percent}%")
    
    def reset_view(self):
        self.image_label.reset_view()
        self.update_zoom_label()
    
    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Model", "", "PyTorch Model (*.pt)")
        if path:
            self._load_model_from_path(path)
    
    def load_yolov4_model(self):
        cfg_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLOv4 Config File (.cfg)", "", 
            "Config Files (*.cfg);;All Files (*)"
        )
        if not cfg_path:
            return
        
        base_dir = os.path.dirname(cfg_path)
        cfg_basename = os.path.splitext(os.path.basename(cfg_path))[0]
        
        auto_weights = None
        for f in os.listdir(base_dir):
            if f.endswith('.weights'):
                if cfg_basename.split('_')[0] in f or cfg_basename in f:
                    auto_weights = os.path.join(base_dir, f)
                    break
        
        auto_names = None
        for ext in ['.names', '.txt']:
            for f in os.listdir(base_dir):
                if f.lower().endswith(ext) and 'names' in f.lower():
                    auto_names = os.path.join(base_dir, f)
                    break
            if not auto_names:
                for f in os.listdir(base_dir):
                    if f.lower().endswith(ext) and cfg_basename.split('_')[0] in f:
                        auto_names = os.path.join(base_dir, f)
                        break
        
        weights_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLOv4 Weights File (.weights)", 
            auto_weights if auto_weights else base_dir,
            "Weights Files (*.weights);;All Files (*)"
        )
        if not weights_path:
            return
        
        names_path, _ = QFileDialog.getOpenFileName(
            self, "Select Class Names File (.names or .txt)", 
            auto_names if auto_names else base_dir,
            "Names Files (*.names *.txt);;All Files (*)"
        )
        if not names_path:
            return
        
        if self.model_mgr.load_yolov4_model(cfg_path, weights_path, names_path):
            model_name = self.model_mgr.get_model_name()
            input_size = f"{self.model_mgr.yolov4_input_width}x{self.model_mgr.yolov4_input_height}"
            self.lbl_model_status.setText(f"YOLOv4: {model_name} ({input_size})")
            self.lbl_model_status.setStyleSheet(STATUS_SUCCESS_STYLE)
            
            model_classes = self.model_mgr.get_class_names()
            if model_classes:
                self.class_names = model_classes
                self.update_class_combo()
                
            QMessageBox.information(
                self, "Model Loaded", 
                f"YOLOv4-tiny model loaded successfully!\n\n"
                f"Config: {os.path.basename(cfg_path)}\n"
                f"Weights: {os.path.basename(weights_path)}\n"
                f"Classes: {os.path.basename(names_path)}\n"
                f"Input size: {input_size}\n"
                f"Classes: {len(model_classes)}"
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to load YOLOv4 model.\n\nMake sure the files are valid.")
    
    def auto_load_model(self):
        if os.path.exists(DEFAULT_MODEL_PATH):
            self._load_model_from_path(DEFAULT_MODEL_PATH)
    
    def _load_model_from_path(self, path):
        if self.model_mgr.load_model(path):
            self.lbl_model_status.setText(f"Model: {self.model_mgr.get_model_name()}")
            self.lbl_model_status.setStyleSheet(STATUS_SUCCESS_STYLE)
            
            model_classes = self.model_mgr.get_class_names()
            if model_classes:
                self.class_names = model_classes
                self.update_class_combo()
        else:
            QMessageBox.critical(self, "Error", "Failed to load model")
    
    def load_class_names(self):
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
        name, ok = QInputDialog.getText(self, "Add New Class", "Enter class name:")
        if ok and name.strip():
            name = name.strip()
            new_id = max(self.class_names.keys()) + 1 if self.class_names else 0
            self.class_names[new_id] = name
            self.update_class_combo()
            self.save_classes_to_file()
            QMessageBox.information(self, "Success", f"Added class {new_id}: {name}")
    
    def save_classes_to_file(self):
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
        return self.class_names.get(class_id, f"Class {class_id}")
    
    def open_directory(self):
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
        if not self.image_list:
            return
        annotated = sum(
            1 for img in self.image_list 
            if self.file_mgr.annotation_exists(self.image_folder, img)
        )
        self.progress_bar.setValue(annotated)
    
    def load_image(self):
        if not self.image_list:
            return
        
        filename = self.image_list[self.current_index]
        self.current_image_path = os.path.join(self.image_folder, filename)
        self.original_pixmap = QPixmap(self.current_image_path)
        
        self.image_label.zoom_level = 1.0
        self.image_label.pan_offset_x = 0
        self.image_label.pan_offset_y = 0
        self.update_zoom_label()
        
        self.display_image()
        
        self.lbl_info.setText(f"{filename}  ({self.current_index + 1}/{len(self.image_list)})")
        self.state_mgr.clear()
        
        txt_path = os.path.splitext(self.current_image_path)[0] + ".txt"
        self.annotation_mgr.clear()
        self.raw_detections = []
        
        if os.path.exists(txt_path):
            boxes = self.file_mgr.load_annotations(txt_path)
            self.annotation_mgr.set_boxes(boxes)
            if boxes:
                self.lbl_info.setText(f"{filename}  ({self.current_index + 1}/{len(self.image_list)}) - {len(boxes)} labels loaded")
        elif self.model_mgr.is_loaded():
            self.run_inference()
        
        self.mask_rectangles = []
        self.selected_mask_index = -1
        self.update_mask_list()
        
        self.update_list_widget()
        self.draw_boxes()
    
    def run_inference(self):
        self.raw_detections = self.model_mgr.run_inference(
            self.current_image_path, 
            self.confidence_threshold
        )
        self.apply_confidence_filter()
    
    def apply_confidence_filter(self):
        filtered = self.annotation_mgr.filter_by_confidence(
            self.raw_detections, 
            self.confidence_threshold
        )
        self.annotation_mgr.set_boxes(filtered)
        self.update_list_widget()
        self.draw_boxes()
    
    def on_confidence_changed(self, value):
        self.confidence_threshold = value / 100.0
        self.lbl_conf_value.setText(f"{self.confidence_threshold:.2f}")
        if self.raw_detections:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.apply_confidence_filter()
    
    def display_image(self):
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
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        base_scaled = self.original_pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        zoomed_w = int(base_scaled.width() * zoom)
        zoomed_h = int(base_scaled.height() * zoom)
        zoomed = self.original_pixmap.scaled(zoomed_w, zoomed_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        canvas = QPixmap(self.image_label.size())
        canvas.fill(QColor(COLORS['canvas']))
        
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        draw_x = int(self.offset_x + pan_x)
        draw_y = int(self.offset_y + pan_y)
        painter.drawPixmap(draw_x, draw_y, zoomed)
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        boxes = self.annotation_mgr.get_boxes()
        selected_idx = self.annotation_mgr.selected_index
        
        effective_scale_x = self.scale_factor_x * zoom
        effective_scale_y = self.scale_factor_y * zoom
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(box, orig_w, orig_h, effective_scale_x, effective_scale_y)
            
            if not rect:
                continue
            
            rect.translate(int(adj_offset_x), int(adj_offset_y))
            is_selected = (i == selected_idx)
            
            if is_selected:
                pen = QPen(QColor(0, 200, 255), 2)
            else:
                pen = QPen(QColor(255, 80, 80), 2)
            
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
            
            if is_selected:
                self.draw_handles(painter, rect)
            
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
        
        self._draw_existing_masks_zoomed(painter, orig_w, orig_h, effective_scale_x, effective_scale_y, adj_offset_x, adj_offset_y)
        
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
        hs = HANDLE_SIZE
        handle_color = QColor(255, 255, 255)
        handle_border = QColor(0, 150, 200)
        
        painter.setBrush(QBrush(handle_color))
        painter.setPen(QPen(handle_border, 1))
        
        corners = [
            (rect.left() - hs//2, rect.top() - hs//2),
            (rect.right() - hs//2, rect.top() - hs//2),
            (rect.left() - hs//2, rect.bottom() - hs//2),
            (rect.right() - hs//2, rect.bottom() - hs//2),
        ]
        
        for cx, cy in corners:
            painter.drawRect(cx, cy, hs, hs)
        
        edges = [
            (rect.center().x() - hs//2, rect.top() - hs//2),
            (rect.center().x() - hs//2, rect.bottom() - hs//2),
            (rect.left() - hs//2, rect.center().y() - hs//2),
            (rect.right() - hs//2, rect.center().y() - hs//2),
        ]
        
        for ex, ey in edges:
            painter.drawRect(ex, ey, hs, hs)
    
    def toggle_draw_mode(self):
        if self.mask_mode:
            self.toggle_mask_mode()
        
        self.draw_mode = not self.draw_mode
        if self.draw_mode:
            self.btn_draw_mode.setText("Draw: ON [W]")
            self.btn_draw_mode.setChecked(True)
            self.image_label.setCursor(Qt.CrossCursor)
        else:
            self.btn_draw_mode.setText("Draw: OFF [W]")
            self.btn_draw_mode.setChecked(False)
            self.image_label.setCursor(Qt.ArrowCursor)
    
    def toggle_mask_mode(self):
        if self.draw_mode:
            self.draw_mode = False
            self.btn_draw_mode.setText("Draw: OFF [W]")
            self.btn_draw_mode.setChecked(False)
        
        self.mask_mode = not self.mask_mode
        if self.mask_mode:
            self.btn_mask_mode.setText("Mask: ON [M]")
            self.btn_mask_mode.setChecked(True)
            self.btn_mask_mode.setStyleSheet(f"background-color: #666; color: #ff6666; font-weight: bold;")
            self.image_label.setCursor(Qt.CrossCursor)
        else:
            self.btn_mask_mode.setText("Mask: OFF [M]")
            self.btn_mask_mode.setChecked(False)
            self.btn_mask_mode.setStyleSheet(f"background-color: #555; color: white;")
            self.image_label.setCursor(Qt.ArrowCursor)
    
    def mask_list_selection_changed(self, row):
        self.selected_mask_index = row
        self.annotation_mgr.deselect()
        self.draw_boxes()
    
    def delete_selected_mask(self):
        if 0 <= self.selected_mask_index < len(self.mask_rectangles):
            del self.mask_rectangles[self.selected_mask_index]
            self.selected_mask_index = -1
            self.update_mask_list()
            self.draw_boxes()
    
    def clear_all_masks(self):
        if self.mask_rectangles:
            reply = QMessageBox.question(
                self, "Clear Masks",
                f"Delete all {len(self.mask_rectangles)} masks?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.mask_rectangles = []
                self.selected_mask_index = -1
                self.update_mask_list()
                self.draw_boxes()
    
    def update_mask_list(self):
        self.mask_list.clear()
        for i, mask in enumerate(self.mask_rectangles):
            self.mask_list.addItem(f"Mask {i+1}: ({mask['w']*100:.0f}% x {mask['h']*100:.0f}%)")
    
    def draw_temp_mask(self, start, end):
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        base_scaled = self.original_pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        zoomed_w = int(base_scaled.width() * zoom)
        zoomed_h = int(base_scaled.height() * zoom)
        zoomed = self.original_pixmap.scaled(zoomed_w, zoomed_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        canvas = QPixmap(self.image_label.size())
        canvas.fill(QColor(COLORS['canvas']))
        
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        draw_x = int(self.offset_x + pan_x)
        draw_y = int(self.offset_y + pan_y)
        painter.drawPixmap(draw_x, draw_y, zoomed)
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        effective_scale_x = self.scale_factor_x * zoom
        effective_scale_y = self.scale_factor_y * zoom
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        self._draw_existing_boxes_zoomed(painter, orig_w, orig_h, effective_scale_x, effective_scale_y, adj_offset_x, adj_offset_y)
        self._draw_existing_masks_zoomed(painter, orig_w, orig_h, effective_scale_x, effective_scale_y, adj_offset_x, adj_offset_y)
        
        temp_rect = QRect(
            int(min(start.x(), end.x())), int(min(start.y(), end.y())), 
            int(abs(end.x() - start.x())), int(abs(end.y() - start.y()))
        )
        
        painter.fillRect(temp_rect, QColor(128, 128, 128, 240))
        
        pen = QPen(QColor(200, 200, 200), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(temp_rect)
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(int(min(start.x(), end.x())) + 4, int(min(start.y(), end.y())) + 14, "MASK")
        
        painter.end()
        self.image_label.setPixmap(canvas)
    
    def finalize_new_mask(self, start, end):
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        x1 = (start.x() - adj_offset_x) / zoom
        y1 = (start.y() - adj_offset_y) / zoom
        x2 = (end.x() - adj_offset_x) / zoom
        y2 = (end.y() - adj_offset_y) / zoom
        
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.draw_boxes()
            return
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        
        px_x1, px_y1 = min(x1, x2) / self.scale_factor_x, min(y1, y2) / self.scale_factor_y
        px_x2, px_y2 = max(x1, x2) / self.scale_factor_x, max(y1, y2) / self.scale_factor_y
        
        px_x1 = max(0, min(px_x1, orig_w))
        px_y1 = max(0, min(px_y1, orig_h))
        px_x2 = max(0, min(px_x2, orig_w))
        px_y2 = max(0, min(px_y2, orig_h))
        
        cx = (px_x1 + px_x2) / 2 / orig_w
        cy = (px_y1 + px_y2) / 2 / orig_h
        w = (px_x2 - px_x1) / orig_w
        h = (px_y2 - px_y1) / orig_h
        
        new_mask = {'x': cx, 'y': cy, 'w': w, 'h': h}
        self.mask_rectangles.append(new_mask)
        self.update_mask_list()
        self.draw_boxes()
    
    def _draw_existing_masks(self, painter, orig_w, orig_h):
        for i, mask in enumerate(self.mask_rectangles):
            cx, cy, w, h = mask['x'], mask['y'], mask['w'], mask['h']
            x1 = (cx - w/2) * orig_w * self.scale_factor_x
            y1 = (cy - h/2) * orig_h * self.scale_factor_y
            w_px = w * orig_w * self.scale_factor_x
            h_px = h * orig_h * self.scale_factor_y
            
            rect = QRect(int(x1), int(y1), int(w_px), int(h_px))
            
            painter.fillRect(rect, QColor(128, 128, 128, 255))
            
            if i == self.selected_mask_index:
                pen = QPen(QColor(255, 100, 100), 3)
            else:
                pen = QPen(QColor(100, 100, 100), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
    
    def _draw_existing_masks_zoomed(self, painter, orig_w, orig_h, scale_x, scale_y, offset_x, offset_y):
        for i, mask in enumerate(self.mask_rectangles):
            cx, cy, w, h = mask['x'], mask['y'], mask['w'], mask['h']
            x1 = (cx - w/2) * orig_w * scale_x + offset_x
            y1 = (cy - h/2) * orig_h * scale_y + offset_y
            w_px = w * orig_w * scale_x
            h_px = h * orig_h * scale_y
            
            rect = QRect(int(x1), int(y1), int(w_px), int(h_px))
            
            painter.fillRect(rect, QColor(128, 128, 128, 255))
            
            if i == self.selected_mask_index:
                pen = QPen(QColor(255, 100, 100), 3)
            else:
                pen = QPen(QColor(100, 100, 100), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
    
    def _draw_existing_boxes(self, painter, orig_w, orig_h):
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
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
    
    def _draw_existing_boxes_zoomed(self, painter, orig_w, orig_h, scale_x, scale_y, offset_x, offset_y):
        boxes = self.annotation_mgr.get_boxes()
        selected_idx = self.annotation_mgr.selected_index
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(box, orig_w, orig_h, scale_x, scale_y)
            if rect:
                rect.translate(int(offset_x), int(offset_y))
                pen = QPen(QColor(0, 200, 255), 2) if i == selected_idx else QPen(QColor(255, 80, 80), 2)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
    
    def apply_masks_to_image(self):
        if not self.current_image_path or not self.mask_rectangles:
            return
        
        import cv2
        
        try:
            img = cv2.imread(self.current_image_path)
            if img is None:
                return
            
            h, w = img.shape[:2]
            
            for mask in self.mask_rectangles:
                cx, cy, mw, mh = mask['x'], mask['y'], mask['w'], mask['h']
                x1 = int((cx - mw/2) * w)
                y1 = int((cy - mh/2) * h)
                x2 = int((cx + mw/2) * w)
                y2 = int((cy + mh/2) * h)
                
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                cv2.rectangle(img, (x1, y1), (x2, y2), (128, 128, 128), -1)
            
            cv2.imwrite(self.current_image_path, img)
            self.original_pixmap = QPixmap(self.current_image_path)
            
        except Exception as e:
            print(f"Error applying masks: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to apply masks to image: {e}")
    
    def update_default_class(self, value):
        self.default_class = value
    
    def draw_temp_box(self, start, end):
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        base_scaled = self.original_pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        zoomed_w = int(base_scaled.width() * zoom)
        zoomed_h = int(base_scaled.height() * zoom)
        zoomed = self.original_pixmap.scaled(zoomed_w, zoomed_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        canvas = QPixmap(self.image_label.size())
        canvas.fill(QColor(COLORS['canvas']))
        
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        
        draw_x = int(self.offset_x + pan_x)
        draw_y = int(self.offset_y + pan_y)
        painter.drawPixmap(draw_x, draw_y, zoomed)
        
        orig_w, orig_h = self.original_pixmap.width(), self.original_pixmap.height()
        effective_scale_x = self.scale_factor_x * zoom
        effective_scale_y = self.scale_factor_y * zoom
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        boxes = self.annotation_mgr.get_boxes()
        selected_idx = self.annotation_mgr.selected_index
        for i, box in enumerate(boxes):
            rect = BoxGeometry.get_box_rect_px(box, orig_w, orig_h, effective_scale_x, effective_scale_y)
            if rect:
                rect.translate(int(adj_offset_x), int(adj_offset_y))
                pen = QPen(QColor(0, 200, 255), 2) if i == selected_idx else QPen(QColor(255, 80, 80), 2)
                painter.setPen(pen)
                painter.drawRect(rect)
        
        self._draw_existing_masks_zoomed(painter, orig_w, orig_h, effective_scale_x, effective_scale_y, adj_offset_x, adj_offset_y)
        
        pen = QPen(QColor(0, 180, 255), 2, Qt.DashLine)
        painter.setPen(pen)
        
        temp_rect = QRect(
            int(min(start.x(), end.x())), int(min(start.y(), end.y())), 
            int(abs(end.x() - start.x())), int(abs(end.y() - start.y()))
        )
        painter.drawRect(temp_rect)
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(
            int(min(start.x(), end.x())), int(min(start.y(), end.y())) - 4, 
            f"New: {self.get_class_name(self.default_class)}"
        )
        
        painter.end()
        self.image_label.setPixmap(canvas)
    
    def finalize_new_box(self, start, end):
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        x1 = (start.x() - adj_offset_x) / zoom
        y1 = (start.y() - adj_offset_y) / zoom
        x2 = (end.x() - adj_offset_x) / zoom
        y2 = (end.y() - adj_offset_y) / zoom
        
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
    
    def select_box_at(self, mouse_x, mouse_y):
        if not self.original_pixmap:
            return
        
        zoom = self.image_label.zoom_level
        pan_x = self.image_label.pan_offset_x
        pan_y = self.image_label.pan_offset_y
        
        adj_offset_x = self.offset_x + pan_x
        adj_offset_y = self.offset_y + pan_y
        
        real_x = (mouse_x - adj_offset_x) / zoom
        real_y = (mouse_y - adj_offset_y) / zoom
        
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
            self.selected_mask_index = -1
            self.box_list.setCurrentRow(selected_idx)
            self.update_class_selector(boxes[selected_idx]['class'])
        self.draw_boxes()
    
    def update_list_widget(self):
        self.box_list.clear()
        boxes = self.annotation_mgr.get_boxes()
        sorted_indices = self.annotation_mgr.get_sorted_indices()
        
        for pos, i in enumerate(sorted_indices):
            box = boxes[i]
            self.box_list.addItem(
                f"{pos+1}. {self.get_class_name(box['class'])}  ({box.get('conf', 1.0):.2f})"
            )
    
    def list_selection_changed(self, row):
        boxes = self.annotation_mgr.get_boxes()
        if 0 <= row < len(boxes):
            self.annotation_mgr.select_box(row)
            self.selected_mask_index = -1
            self.update_class_selector(boxes[row]['class'])
            self.draw_boxes()
    
    def update_class_selector(self, class_id):
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
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0 and self.class_names:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            new_class = self.combo_class.itemData(index)
            self.annotation_mgr.update_box_class(selected_idx, new_class)
            self.update_list_widget()
            self.box_list.setCurrentRow(selected_idx)
            self.draw_boxes()
    
    def update_current_box_class_spin(self):
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0 and not self.class_names:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.annotation_mgr.update_box_class(selected_idx, self.spin_class.value())
            self.update_list_widget()
            self.box_list.setCurrentRow(selected_idx)
            self.draw_boxes()
    
    def delete_current_box(self):
        selected_idx = self.annotation_mgr.selected_index
        if selected_idx >= 0:
            self.state_mgr.save_state(self.annotation_mgr.get_boxes())
            self.annotation_mgr.delete_box(selected_idx)
            self.update_list_widget()
            self.draw_boxes()
    
    def sort_boxes_left_to_right(self):
        boxes = self.annotation_mgr.get_boxes()
        if not boxes:
            return
        self.state_mgr.save_state(boxes)
        self.annotation_mgr.sort_boxes_by_x()
        self.update_list_widget()
        self.draw_boxes()
    
    def undo(self):
        boxes = self.annotation_mgr.get_boxes()
        prev_state = self.state_mgr.undo(boxes)
        if prev_state is not None:
            self.annotation_mgr.set_boxes(prev_state)
            self.update_list_widget()
            self.draw_boxes()
    
    def redo(self):
        boxes = self.annotation_mgr.get_boxes()
        next_state = self.state_mgr.redo(boxes)
        if next_state is not None:
            self.annotation_mgr.set_boxes(next_state)
            self.update_list_widget()
            self.draw_boxes()
    
    def save_annotation(self, go_next=True):
        if not self.current_image_path:
            return
        
        masks_applied = False
        if self.mask_rectangles:
            self.apply_masks_to_image()
            masks_applied = True
            self.mask_rectangles = []
            self.update_mask_list()
        
        txt_path = os.path.splitext(self.current_image_path)[0] + ".txt"
        boxes = self.annotation_mgr.get_boxes()
        self.file_mgr.save_annotations(txt_path, boxes)
        
        self.lbl_info.setText("Saved" + (" (masks applied)" if masks_applied else ""))
        self.update_progress()
        QApplication.processEvents()
        
        if go_next and self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    def next_image(self):
        self.save_annotation(go_next=False)
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
    
    def skip_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_image()
    
    def find_first_unannotated(self):
        for i, img in enumerate(self.image_list):
            if not self.file_mgr.annotation_exists(self.image_folder, img):
                return i
        return -1
    
    def find_next_unannotated(self, start_from=None):
        start = start_from if start_from is not None else self.current_index + 1
        
        for i in range(start, len(self.image_list)):
            if not self.file_mgr.annotation_exists(self.image_folder, self.image_list[i]):
                return i
        for i in range(0, start):
            if not self.file_mgr.annotation_exists(self.image_folder, self.image_list[i]):
                return i
        return -1
    
    def goto_next_unannotated(self):
        if not self.image_list:
            return
        next_idx = self.find_next_unannotated()
        if next_idx >= 0:
            self.current_index = next_idx
            self.load_image()
        else:
            QMessageBox.information(self, "Complete", "All images have been annotated.")
    
    def delete_current_image(self):
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
    
    def keyPressEvent(self, event):
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
        elif key == Qt.Key_M:
            self.toggle_mask_mode()
        elif key == Qt.Key_R:
            self.reset_view()
        elif key == Qt.Key_Q:
            self.skip_image()
        elif key == Qt.Key_N:
            self.goto_next_unannotated()
        elif key == Qt.Key_X:
            self.delete_current_image()
        elif key == Qt.Key_Escape:
            if self.draw_mode:
                self.toggle_draw_mode()
            elif self.mask_mode:
                self.toggle_mask_mode()
            else:
                self.annotation_mgr.deselect()
                self.selected_mask_index = -1
                self.draw_boxes()
        elif key == Qt.Key_Delete:
            if self.selected_mask_index >= 0:
                self.delete_selected_mask()
            else:
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
