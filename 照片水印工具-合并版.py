# -*- coding: utf-8 -*-
"""
照片水印添加工具 V3.0 (by:Ragnar)
作者: Ragnar
功能: 为照片添加带文件夹水印，支持自定义地点和时间模式
界面设计: 专业商务风格
"""

import os
import threading
import random
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QGraphicsDropShadowEffect, QFrame,
    QApplication, QScrollArea, QSizePolicy, QDateTimeEdit, QDateEdit, QRadioButton,
    QColorDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QBrush, QPainter, QPen
from PIL import Image, ImageDraw, ImageFont, ExifTags


class ProcessingThread(QThread):
    progress_update = pyqtSignal(int, str, int, int)
    processing_complete = pyqtSignal(int)
    processing_error = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(self, folder_path, location, use_custom_time, start_time=None, end_time=None, watermark_height_ratio=10, watermark_color="white", parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.location = location
        self.use_custom_time = use_custom_time
        self.start_time = start_time
        self.end_time = end_time
        self.watermark_height_ratio = watermark_height_ratio
        self.watermark_color = watermark_color
        self.processing = True
        self.paused = False

    def run(self):
        try:
            image_files = []
            for root, dirs, files in os.walk(self.folder_path):
                for filename in files:
                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                        image_files.append(os.path.join(root, filename))

            total = len(image_files)
            if total == 0:
                self.processing_error.emit("未找到图片文件！")
                return

            processed = 0
            for file_path in image_files:
                if not self.processing:
                    self.log_message.emit("处理已停止")
                    break
                
                # 检查是否暂停
                while self.paused:
                    if not self.processing:
                        self.log_message.emit("处理已停止")
                        return
                    self.msleep(100)

                filename = os.path.basename(file_path)
                self.log_message.emit(f"正在处理: {filename}")

                try:
                    self.add_watermark(file_path)
                    processed += 1
                    progress = int((processed / total) * 100)
                    self.progress_update.emit(progress, f"已处理 {processed}/{total}", processed, total)
                except Exception as e:
                    self.log_message.emit(f"处理失败 {filename}: {str(e)}")

            if self.processing:
                self.processing_complete.emit(processed)

        except Exception as e:
            self.processing_error.emit(str(e))

    def stop(self):
        self.processing = False
        self.paused = False
        
    def pause(self):
        self.paused = True
        
    def resume(self):
        self.paused = False

    def add_watermark(self, image_path):
        image = Image.open(image_path)
        width, height = image.size

        if self.use_custom_time:
            # 生成开始时间和结束时间之间的随机时间
            time_diff = self.end_time - self.start_time
            random_seconds = random.randint(0, int(time_diff.total_seconds()))
            creation_time = self.start_time + timedelta(seconds=random_seconds)
        else:
            # 使用原始时间
            try:
                exif = image._getexif()
                if exif:
                    for tag, value in exif.items():
                        if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                            creation_time = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            break
                    else:
                        creation_time = datetime.fromtimestamp(os.path.getctime(image_path))
                else:
                    creation_time = datetime.fromtimestamp(os.path.getctime(image_path))
            except (AttributeError, KeyError, ValueError):
                creation_time = datetime.fromtimestamp(os.path.getctime(image_path))

        year_str = creation_time.strftime("%Y")
        month_str = creation_time.strftime("%m")
        day_str = creation_time.strftime("%d")
        hour_str = creation_time.strftime("%H")
        minute_str = creation_time.strftime("%M")

        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        day_of_week = "备注：" + weekdays[creation_time.weekday()]

        watermark_text = [
            ("时间：", year_str, "年", month_str, "月", day_str, "日", hour_str, "时", minute_str, "分"),
            f"地点：{self.location}",
            day_of_week
        ]

        draw = ImageDraw.Draw(image)

        if height > width:
            watermark_height = int(height / self.watermark_height_ratio)
        else:
            watermark_height = int(height / (self.watermark_height_ratio * 0.8))
        font_size = int(watermark_height / 3)

        try:
            chinese_font = ImageFont.truetype("simsun.ttc", font_size)
        except:
            chinese_font = ImageFont.load_default()

        try:
            latin_font = ImageFont.truetype("times.ttf", font_size)
        except:
            latin_font = chinese_font

        text_height = font_size * 3
        x = font_size // 2
        y = height - text_height - font_size // 2

        for i, text_item in enumerate(watermark_text):
            current_x = x
            current_y = y + i * font_size

            if i == 0:
                for part in text_item:
                    if part.isdigit():
                        draw.text((current_x, current_y), part, font=latin_font, fill=self.watermark_color)
                        current_x += latin_font.getlength(part)
                    else:
                        draw.text((current_x, current_y), part, font=chinese_font, fill=self.watermark_color)
                        current_x += chinese_font.getlength(part)
            else:
                draw.text((current_x, current_y), text_item, font=chinese_font, fill=self.watermark_color)

        image.save(image_path)


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.setStyleSheet("""
            QFrame#ModernCard {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E8E8E8;
            }
        """)


class WatermarkAppUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processing_thread = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("照片水印添加工具 V3.0")
        self.setFixedSize(720, 920)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        self.center_window()

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 247, 250))
        self.setPalette(palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(10)

        header_card = ModernCard()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel("照片水印添加工具 V3.0")
        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1A1A2E; background: transparent;")

        author_label = QLabel("作者：Ragnar  |  联系方式：ragnar5218@163.com")
        author_font = QFont("Microsoft YaHei", 8)
        author_label.setFont(author_font)
        author_label.setStyleSheet("color: #888888; background: transparent;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(author_label)

        main_layout.addWidget(header_card)

        config_card = ModernCard()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(16, 14, 16, 14)
        config_layout.setSpacing(10)

        config_title = QLabel("配置信息")
        config_title_font = QFont("Microsoft YaHei", 13, QFont.Medium)
        config_title.setFont(config_title_font)
        config_title.setStyleSheet("color: #333333; background: transparent;")

        folder_layout = QHBoxLayout()
        folder_label = QLabel("📁 选择文件夹")
        folder_label.setFont(QFont("Microsoft YaHei", 10))
        folder_label.setStyleSheet("color: #555555; background: transparent;")
        folder_label.setFixedWidth(120)

        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("点击右侧按钮选择照片文件夹")
        self.folder_input.setFont(QFont("Microsoft YaHei", 10))
        self.folder_input.setStyleSheet("""
            QLineEdit {
                background: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 10px 12px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #4A90D9;
                background: #FFFFFF;
            }
        """)
        self.folder_input.setReadOnly(True)
        self.folder_input.setFixedHeight(36)
        self.folder_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.folder_btn = QPushButton("浏览")
        self.folder_btn.setFont(QFont("Microsoft YaHei", 10))
        self.folder_btn.setCursor(Qt.PointingHandCursor)
        self.folder_btn.setFixedSize(70, 36)
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: medium;
            }
            QPushButton:hover {
                background: #3A7BC8;
            }
            QPushButton:pressed {
                background: #2E6BA8;
            }
        """)
        self.folder_btn.clicked.connect(self.select_folder)

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)

        location_layout = QHBoxLayout()
        location_label = QLabel("📍 地点名称")
        location_label.setFont(QFont("Microsoft YaHei", 10))
        location_label.setStyleSheet("color: #555555; background: transparent;")
        location_label.setFixedWidth(100)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("输入地点名称，如：北京故宫")
        self.location_input.setFont(QFont("Microsoft YaHei", 10))
        self.location_input.setStyleSheet("""
            QLineEdit {
                background: #FFFFFF;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #4A90D9;
            }
        """)
        self.location_input.setFixedHeight(36)

        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_input)

        # 水印颜色选择
        color_layout = QHBoxLayout()
        color_label = QLabel("🎨 水印颜色")
        color_label.setFont(QFont("Microsoft YaHei", 10))
        color_label.setStyleSheet("color: #555555; background: transparent;")
        color_label.setFixedWidth(100)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(36, 36)
        self.color_preview.setStyleSheet("background: #FFFFFF; border: 1px solid #DEE2E6; border-radius: 6px;")
        self.current_color = QColor(255, 255, 255)

        self.color_btn = QPushButton("选择颜色")
        self.color_btn.setFont(QFont("Microsoft YaHei", 10))
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self.color_btn.setFixedSize(90, 36)
        self.color_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: medium;
            }
            QPushButton:hover {
                background: #3A7BC8;
            }
            QPushButton:pressed {
                background: #2E6BA8;
            }
        """)
        self.color_btn.clicked.connect(self.select_color)

        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()

        # 预设颜色版
        preset_layout = QHBoxLayout()
        preset_label = QLabel("预设颜色")
        preset_label.setFont(QFont("Microsoft YaHei", 10))
        preset_label.setStyleSheet("color: #555555; background: transparent;")
        preset_label.setFixedWidth(100)

        self.preset_colors = [
            ("白色", "#FFFFFF"),
            ("黑色", "#000000"),
            ("红色", "#FF0000"),
            ("橙色", "#FFA500"),
            ("黄色", "#FFFF00"),
            ("绿色", "#00FF00"),
            ("青色", "#00FFFF"),
            ("蓝色", "#0000FF"),
            ("紫色", "#800080"),
            ("粉色", "#FFC0CB"),
        ]
        self.preset_buttons = []
        for name, hex_code in self.preset_colors:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_code};
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border: 2px solid #4A90D9;
                }}
            """)
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, c=hex_code: self.set_preset_color(c))
            self.preset_buttons.append(btn)
            preset_layout.addWidget(btn)

        preset_layout.addStretch()

        # 时间模式选择
        time_mode_layout = QHBoxLayout()
        time_mode_label = QLabel("🕒 时间模式")
        time_mode_label.setFont(QFont("Microsoft YaHei", 10))
        time_mode_label.setStyleSheet("color: #555555; background: transparent;")
        time_mode_label.setFixedWidth(100)

        self.original_time_radio = QRadioButton("使用拍摄时间")
        self.original_time_radio.setFont(QFont("Microsoft YaHei", 10))
        self.original_time_radio.setStyleSheet("color: #333333; background: transparent;")
        self.original_time_radio.setChecked(True)
        self.original_time_radio.toggled.connect(self.toggle_time_inputs)

        self.custom_time_radio = QRadioButton("使用自定义时间")
        self.custom_time_radio.setFont(QFont("Microsoft YaHei", 10))
        self.custom_time_radio.setStyleSheet("color: #333333; background: transparent;")
        self.custom_time_radio.toggled.connect(self.toggle_time_inputs)

        time_mode_radio_layout = QHBoxLayout()
        time_mode_radio_layout.addWidget(self.original_time_radio)
        time_mode_radio_layout.addSpacing(30)
        time_mode_radio_layout.addWidget(self.custom_time_radio)

        time_mode_layout.addWidget(time_mode_label)
        time_mode_layout.addSpacing(10)
        time_mode_layout.addLayout(time_mode_radio_layout)
        time_mode_layout.addStretch()

        # 自定义时间输入容器
        self.time_input_container = QWidget()
        self.time_input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        time_input_layout = QVBoxLayout(self.time_input_container)
        time_input_layout.setContentsMargins(0, 0, 0, 0)
        time_input_layout.setSpacing(8)

        # 日期选择
        self.date_layout = QHBoxLayout()
        date_label = QLabel("📅 选择日期")
        date_label.setFont(QFont("Microsoft YaHei", 10))
        date_label.setStyleSheet("color: #555555; background: transparent;")
        date_label.setFixedWidth(100)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setFont(QFont("Microsoft YaHei", 10))
        self.date_input.setStyleSheet("""
            QDateEdit {
                background: #FFFFFF;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333;
            }
            QDateEdit:focus {
                border: 2px solid #4A90D9;
            }
        """)
        self.date_input.setFixedHeight(36)
        self.date_input.setDate(datetime.now().date())

        self.date_layout.addWidget(date_label)
        self.date_layout.addWidget(self.date_input)

        # 最早时间
        self.start_time_layout = QHBoxLayout()
        start_time_label = QLabel("⏰ 最早时间")
        start_time_label.setFont(QFont("Microsoft YaHei", 10))
        start_time_label.setStyleSheet("color: #555555; background: transparent;")
        start_time_label.setFixedWidth(100)

        self.start_time_input = QDateTimeEdit()
        self.start_time_input.setCalendarPopup(False)
        self.start_time_input.setDisplayFormat("HH:mm")
        self.start_time_input.setFont(QFont("Microsoft YaHei", 10))
        self.start_time_input.setStyleSheet("""
            QDateTimeEdit {
                background: #FFFFFF;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333;
            }
            QDateTimeEdit:focus {
                border: 2px solid #4A90D9;
            }
        """)
        self.start_time_input.setFixedHeight(36)
        # 设置最早时间为当天的00:00
        self.start_time_input.setDateTime(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))

        self.start_time_layout.addWidget(start_time_label)
        self.start_time_layout.addWidget(self.start_time_input)

        # 最晚时间
        self.end_time_layout = QHBoxLayout()
        end_time_label = QLabel("⏰ 最晚时间")
        end_time_label.setFont(QFont("Microsoft YaHei", 10))
        end_time_label.setStyleSheet("color: #555555; background: transparent;")
        end_time_label.setFixedWidth(100)

        self.end_time_input = QDateTimeEdit()
        self.end_time_input.setCalendarPopup(False)
        self.end_time_input.setDisplayFormat("HH:mm")
        self.end_time_input.setFont(QFont("Microsoft YaHei", 10))
        self.end_time_input.setStyleSheet("""
            QDateTimeEdit {
                background: #FFFFFF;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333;
            }
            QDateTimeEdit:focus {
                border: 2px solid #4A90D9;
            }
        """)
        self.end_time_input.setFixedHeight(36)
        # 设置最晚时间为当天的23:59
        self.end_time_input.setDateTime(datetime.now().replace(hour=23, minute=59, second=0, microsecond=0))

        self.end_time_layout.addWidget(end_time_label)
        self.end_time_layout.addWidget(self.end_time_input)

        # 将时间输入布局添加到容器
        time_input_layout.addLayout(self.date_layout)
        time_input_layout.addLayout(self.start_time_layout)
        time_input_layout.addLayout(self.end_time_layout)

        config_layout.addWidget(config_title)
        config_layout.addLayout(folder_layout)
        config_layout.addLayout(location_layout)
        config_layout.addLayout(color_layout)
        config_layout.addLayout(preset_layout)
        config_layout.addLayout(time_mode_layout)
        config_layout.addWidget(self.time_input_container)

        config_card.setLayout(config_layout)
        main_layout.addWidget(config_card)

        progress_card = ModernCard()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(16, 12, 16, 12)
        progress_layout.setSpacing(8)

        progress_title = QLabel("处理进度")
        progress_title.setFont(QFont("Microsoft YaHei", 13, QFont.Medium))
        progress_title.setStyleSheet("color: #333333; background: transparent;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont("Microsoft YaHei", 8))
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #E9ECEF;
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A90D9, stop:1 #67B0E8);
                border-radius: 4px;
            }
        """)
        self.progress_bar.setValue(0)

        self.progress_label = QLabel("就绪")
        self.progress_label.setFont(QFont("Microsoft YaHei", 9))
        self.progress_label.setStyleSheet("color: #888888; background: transparent;")

        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)

        main_layout.addWidget(progress_card)

        button_card = ModernCard()
        button_layout = QHBoxLayout(button_card)
        button_layout.setContentsMargins(16, 12, 16, 12)

        self.start_btn = QPushButton("开始添加")
        self.start_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(38)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #28A745;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #218838;
            }
            QPushButton:pressed {
                background: #1E7E34;
            }
            QPushButton:disabled {
                background: #CCC;
            }
        """)
        self.start_btn.clicked.connect(self.start_processing)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setFixedHeight(38)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #FFC107;
                color: #212529;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #E0A800;
            }
            QPushButton:pressed {
                background: #D39E00;
            }
            QPushButton:disabled {
                background: #CCC;
            }
        """)
        self.pause_btn.clicked.connect(self.pause_processing)

        self.resume_btn = QPushButton("继续")
        self.resume_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
        self.resume_btn.setCursor(Qt.PointingHandCursor)
        self.resume_btn.setFixedHeight(38)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setStyleSheet("""
            QPushButton {
                background: #17A2B8;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #138496;
            }
            QPushButton:pressed {
                background: #117A8B;
            }
            QPushButton:disabled {
                background: #CCC;
            }
        """)
        self.resume_btn.clicked.connect(self.resume_processing)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setFixedHeight(38)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #DC3545;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #C82333;
            }
            QPushButton:pressed {
                background: #BD2130;
            }
            QPushButton:disabled {
                background: #CCC;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_processing)

        button_layout.addWidget(self.start_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.pause_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.resume_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.stop_btn)

        main_layout.addWidget(button_card)

        log_card = ModernCard()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 12, 16, 12)
        log_layout.setSpacing(8)

        log_title = QLabel("处理日志")
        log_title.setFont(QFont("Microsoft YaHei", 13, QFont.Medium))
        log_title.setStyleSheet("color: #333333; background: transparent;")

        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #F8F9FA;
                color: #333333;
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        self.log_text.setMinimumHeight(100)

        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_card)

        main_layout.addStretch()

        # 初始状态下隐藏自定义时间输入
        self.toggle_time_inputs()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def toggle_time_inputs(self):
        use_custom = self.custom_time_radio.isChecked()
        # 显示/隐藏整个时间输入容器
        self.time_input_container.setVisible(use_custom)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择照片文件夹")
        if folder:
            self.folder_input.setText(folder)
            self.log(f"已选择文件夹: {folder}")

    def select_color(self):
        """打开颜色选择对话框"""
        color = QColorDialog.getColor(self.current_color, self, "选择水印颜色")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(
                f"background: {color.name()}; border: 1px solid #DEE2E6; border-radius: 6px;"
            )
            self.log(f"已选择水印颜色: {color.name()}")

    def set_preset_color(self, hex_code):
        """设置预设颜色"""
        self.current_color = QColor(hex_code)
        self.color_preview.setStyleSheet(
            f"background: {hex_code}; border: 1px solid #DEE2E6; border-radius: 6px;"
        )
        self.log(f"已选择水印颜色: {hex_code}")

    def log(self, message):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_processing(self):
        folder = self.folder_input.text()
        location = self.location_input.text()
        use_custom_time = self.custom_time_radio.isChecked()
        start_datetime = None
        end_datetime = None

        if use_custom_time:
            # 获取日期
            selected_date = self.date_input.date().toPyDate()
            
            # 获取时间
            start_time = self.start_time_input.dateTime().toPyDateTime()
            end_time = self.end_time_input.dateTime().toPyDateTime()
            
            # 组合日期和时间
            start_datetime = datetime.combine(selected_date, start_time.time())
            end_datetime = datetime.combine(selected_date, end_time.time())

        if not folder:
            QMessageBox.warning(self, "警告", "请先选择文件夹！")
            return

        if not location:
            QMessageBox.warning(self, "警告", "请输入地点名称！")
            return

        if use_custom_time and start_datetime > end_datetime:
            QMessageBox.warning(self, "警告", "最早时间不能晚于最晚时间！")
            return

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log("开始添加水印...")

        # 获取当前选择的颜色名称（PIL支持的颜色格式）
        watermark_color = self.current_color.name()

        self.processing_thread = ProcessingThread(
            folder, location, use_custom_time, start_datetime, end_datetime, 10, watermark_color
        )
        self.processing_thread.progress_update.connect(self.on_progress_update)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.processing_error.connect(self.on_processing_error)
        self.processing_thread.log_message.connect(self.log)
        self.processing_thread.start()

    def pause_processing(self):
        if self.processing_thread:
            self.processing_thread.pause()
            self.log("处理已暂停")
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

    def resume_processing(self):
        if self.processing_thread:
            self.processing_thread.resume()
            self.log("处理已继续")
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

    def stop_processing(self):
        if self.processing_thread:
            self.processing_thread.stop()
            self.log("正在停止处理...")

    def on_progress_update(self, value, text, processed, total):
        self.progress_bar.setValue(value)
        self.progress_label.setText(text)

    def on_processing_complete(self, count):
        self.log(f"处理完成！共处理 {count} 张图片")
        QMessageBox.information(self, "完成", f"成功处理 {count} 张图片！")
        self.reset_ui()

    def on_processing_error(self, error):
        QMessageBox.critical(self, "错误", f"处理失败: {error}")
        self.log(f"错误: {error}")
        self.reset_ui()

    def reset_ui(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("就绪")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    window = WatermarkAppUI()
    window.show()

    sys.exit(app.exec_())
