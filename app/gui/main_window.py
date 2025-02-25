from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QCheckBox, QButtonGroup, QRadioButton, QApplication, QGraphicsRectItem, QGraphicsDropShadowEffect)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPen, QFont, QPainter
import threading
from app.gui.styleSheet import STYLE_SHEET
import yaml
import sys
import pandas as pd
import time

from src.alert.detect import detect_anomalies
THRESHOLD_STEP = 100
OUTPUT_CSV = "src/alert/preprocess_data.csv"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()  

        #font
        self.font_size = 10
        self.font = QFont()
        self.font.setFamily("Arial")
        self.font.setPointSize(self.font_size)
        self.app = QApplication(sys.argv)
        self.app.setFont(self.font)

        #overview label initialization
        self.cpu_percent = QLabel("Cpu Usage: --")
        #self.cpu_temp_label = QLabel("--")
        self.current_processes = []
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")
        self.network_label = QLabel("Network Usage: --")

        # Initialize data series for graphs
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.disk_series = QLineSeries()
        self.network_series = QLineSeries()
        #self.cpu_temp_series = QLineSeries()
        self.data_points = 0
        self.max_data_points = 50

        # Create charts
        self.cpu_chart = QChart()
        self.memory_chart = QChart()
        self.disk_chart = QChart()
        self.network_chart = QChart()
        #self.cpu_temp_chart = QChart()
        
        self.setup_ui()  

    def set_theme(self, mode='dark'):
        colors = STYLE_SHEET[mode]
        
        # Main window and tab widget styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background_color']};
                border: 1px solid {colors['border_color']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors['border_color']};
                background-color: {colors['background_color']};
            }}
            
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            
            QTabBar::tab {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                padding: 8px 20px;
                border: 1px solid {colors['border_color']};
                border-bottom: none;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['grid_color']};
                border-bottom: none;
            }}
            
            QTabBar::tab:hover {{
                background-color: {colors['grid_color']};
            }}
        """)
        
        # Charts styling
        charts = [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]
        for chart in charts:
            chart.setTitleBrush(QBrush(QColor(colors["text_color"])))
            chart.setPlotAreaBackgroundBrush(QBrush(QColor(colors["chart_background"])))
            chart.setPlotAreaBackgroundVisible(True)
                        
            # Update chart axes
            for axis in chart.axes():
                axis.setLabelsColor(QColor(colors["axis_labels"]))
                axis.setGridLineColor(QColor(colors["grid_lines"]))
                if isinstance(axis, QValueAxis):
                    pen = QPen(QColor(colors["axis_color"]))
                    axis.setLinePen(pen)
            chart.setBackgroundVisible(False)
            chart.setPlotAreaBackgroundVisible(True)
            
            # Update series colors
            for series in chart.series():
                pen = QPen(QColor(colors["line"]))
                pen.setWidth(self.load_config()['gui']['pen_thickness'])
                series.setPen(pen)
        
            chart_view = self.findChild(QChartView, chart.objectName())
            for chart_view in self.findChildren(QChartView):
                if chart_view:
                    chart_view.setBackgroundBrush(QBrush(QColor(colors["chart_background"])))
                    chart_view.setStyleSheet(f"""
                        QChartView {{
                            background-color: {colors['chart_background']};
                            border: 2px solid {colors['border_color']};
                            border-radius: 4px;
                            border-radius: 8px;
                            padding: 10px;
                            margin: 5px;
                        }}
                    """)
                shadow = chart_view.graphicsEffect()
                if shadow:
                    shadow.setColor(QColor(0, 0, 0, 80) if mode == 'light' else QColor(0, 0, 0, 120))

        # Labels styling
        labels = [self.cpu_percent, self.memory_label, self.disk_label, self.network_label]
        label_style = f"""
            QLabel {{
                color: {colors['label_text_color']};
                border: none;
                padding: 5px;
            }}
        """
        for label in labels:
            label.setStyleSheet(label_style)
        
        button_style = f"""
            QPushButton {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                border: 1px solid {colors['border_color']};
                padding: 5px 15px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['grid_color']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['border_color']};
            }}
        """
        self.show_all_button.setStyleSheet(button_style)
        self.detect_button.setStyleSheet(button_style)

        # Tables styling
        tables = [
            self.process_table, self.cpu_table, self.memory_table, 
            self.disk_table, self.network_table, self.battery_table,
            self.anomaly_table
        ]
        
        table_style = f"""
            QTableWidget {{
                background-color: {colors['table_background']};
                color: {colors['table_text_color']};
                gridline-color: {colors['border_color']};
                border: 1px solid {colors['border_color']};
            }}
            
            QTableWidget::item {{
                padding: 5px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {colors['grid_color']};
                color: {colors['text_color']};
            }}
            
            QHeaderView::section {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                border: 1px solid {colors['border_color']};
                padding: 5px;
            }}
            
            QHeaderView::section:vertical {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
            }}
            
            QTableCornerButton::section {{
                background-color: {colors['background_color']};
                border: 1px solid {colors['border_color']};
            }}
            
            QScrollBar:vertical {{
                background: {colors['background_color']};
                border: 1px solid {colors['border_color']};
                width: 15px;
                margin: 15px 0 15px 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {colors['grid_color']};
                min-height: 30px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background: {colors['background_color']};
                border: 1px solid {colors['border_color']};
                height: 15px;
                margin: 0 15px 0 15px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {colors['grid_color']};
                min-width: 30px;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: none;
            }}
            """     
        for table in tables:
            table.setStyleSheet(table_style)
            
            # Fix index column styling
            for i in range(table.rowCount()):
                index_item = table.verticalHeaderItem(i)
                if index_item:
                    index_item.setForeground(QBrush(QColor(colors['text_color'])))
        
        # Settings widget styling
        settings_style = f"""
            QWidget {{
                background-color: {colors['background_color']};
                color: {colors['table_text_color']};
            }}
            
            QComboBox {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                border: 1px solid {colors['border_color']};
                padding: 5px;
                min-width: 100px;
            }}
            
            QComboBox::drop-down {{
                border: 1px solid {colors['border_color']};
            }}
            
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            
            QComboBox:hover {{
                background-color: {colors['grid_color']};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                selection-background-color: {colors['grid_color']};
                selection-color: {colors['text_color']};
                border: 1px solid {colors['border_color']};
            }}
        """

        self.last_run_time.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {colors['text_color']};
                padding: 5px;
            }}
        """)

        self.settings_widget.setStyleSheet(settings_style)
        
        if hasattr(self, 'overview_tab'):
            self.overview_tab.setStyleSheet(overview_style)

    def set_dark_mode(self):
        """Switch to dark mode"""
        self.set_theme('dark')

    def set_light_mode(self):
        """Switch to light mode"""
        self.set_theme('light')

    def load_config(self):
        with open('config/config.yaml', 'r') as file:
            return yaml.safe_load(file)    

    def setup_chart(self, chart, series, title, y_axis_max, y_axis_tick_count=6):
        config = self.load_config()
        colors = STYLE_SHEET["dark"]  # Default to dark theme initially

        # Set unique object name for the chart
        chart.setObjectName(f"{title.lower().replace(' ', '_')}_chart")
        
        # Create and style the chart view
        chart_view = QChartView(chart)
        chart_view.setObjectName(f"{title.lower().replace(' ', '_')}_view")
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setBackgroundBrush(QBrush(QColor(colors["chart_background"])))


        # Add container widget for border
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(1, 1, 1, 1)
        container_layout.addWidget(chart_view)
        
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['chart_background']};
                border: 2px solid {colors['border_color']};
            }}
        """)

        chart.setPlotAreaBackgroundBrush(QBrush(QColor(colors["chart_background"])))
        chart.setPlotAreaBackgroundVisible(True)

        # Set up series
        series.setColor(QColor(colors['line']))
        chart.addSeries(series)
        
        # Chart configuration
        chart.setBackgroundVisible(False)  # Disable background
        chart.setTitleBrush(QBrush(QColor(colors['text_color'])))
        chart.legend().hide()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Configure axes
        axis_x = QValueAxis()
        axis_y = QValueAxis()
        
        # X-axis setup
        axis_x.setLabelsVisible(False)
        axis_x.setRange(0, self.max_data_points)
        axis_x.setGridLineColor(QColor(colors['chart_grid']))
        axis_x.setLabelsColor(QColor(colors['axis_labels']))
        axis_x.setGridLineVisible(False)
        axis_x.setLabelsVisible(False)
        axis_x.setTickCount(0)
        pen_x = QPen(QColor(colors["axis_color"]))
        axis_x.setLinePen(pen_x)
        
        # Y-axis setup
        axis_y.setRange(0, y_axis_max)
        axis_y.setTickCount(y_axis_tick_count)
        axis_y.setGridLineColor(QColor(colors['chart_grid']))
        axis_y.setLabelsColor(QColor(colors['axis_labels']))
        pen_y = QPen(QColor(colors["axis_color"]))
        axis_y.setLinePen(pen_y)
        
        # Attach axes
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        # Series line style
        pen = QPen(QColor(colors['line']))
        pen.setWidth(config['gui']['pen_thickness'])
        series.setPen(pen)

        return container, axis_y


    def setup_ui(self):
        config = self.load_config()
        colors = STYLE_SHEET["dark"]
        self.max_count = config['monitoring']['process']['max_count']

        self.setWindowTitle("VitalWatch")
        self.setMinimumSize(820, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # overview tab
        overview_widget = QWidget()
        overview_layout = QGridLayout(overview_widget)

        # charts
        cpu_chart_view, _ = self.setup_chart(self.cpu_chart, self.cpu_series, "CPU Usage %", y_axis_max=100)
        memory_chart_view, _ = self.setup_chart(self.memory_chart, self.memory_series, "Memory Usage %", y_axis_max=100)
        disk_chart_view, _ = self.setup_chart(self.disk_chart, self.disk_series, "Disk Usage %", y_axis_max=100)
    
        self.max_network_value = 100
        network_chart_view, self.network_y = self.setup_chart(self.network_chart, self.network_series, "Network Usage Kbps", y_axis_max=self.max_network_value)

        # Add labels to overview tab
        overview_layout.addWidget(self.cpu_percent, 0, 0)
        overview_layout.addWidget(cpu_chart_view, 1, 0)
        overview_layout.addWidget(self.memory_label, 0, 1)
        overview_layout.addWidget(memory_chart_view, 1, 1)
        overview_layout.addWidget(self.disk_label, 2, 0)
        overview_layout.addWidget(disk_chart_view, 3, 0)        
        overview_layout.addWidget(self.network_label, 2, 1)
        overview_layout.addWidget(network_chart_view, 3, 1)       
        #tabs.addTab(overview_widget, "Overview")

        # Anomaly Detection tab
        anomaly_widget = QWidget()
        anomaly_layout = QVBoxLayout(anomaly_widget)

        # Add status label above
        self.anomaly_status = QLabel("System Status: Not Checked")
        self.anomaly_status.setAlignment(Qt.AlignCenter)
        self.anomaly_status.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                background-color: #7f8c8d;
                color: white;
            }
        """)

        # Add last run time label
        self.last_run_time = QLabel("Last Run: Never")
        self.last_run_time.setAlignment(Qt.AlignCenter)

        # Create button to trigger detection
        self.detect_button = QPushButton("Run Anomaly Detection")
        self.detect_button.clicked.connect(self.on_detect_clicked)

        # Create horizontal container for button and last run time
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignCenter)

        # Add widgets to horizontal layout with spacing
        button_layout.addWidget(self.detect_button)
        button_layout.addWidget(self.last_run_time)

        # Set equal stretch for both widgets
        button_layout.setStretchFactor(self.detect_button, 1)
        button_layout.setStretchFactor(self.last_run_time, 1)

        # Create table for results
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(5)  # Adjust columns based on your metrics
        self.anomaly_table.setHorizontalHeaderLabels(['CPU %', 'Memory %', 'Disk %', 'Network', 'Status'])
        self.anomaly_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Style the table header
        anomaly_header = self.anomaly_table.horizontalHeader()
        for i in range(self.anomaly_table.columnCount()):
            anomaly_header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.anomaly_table.verticalHeader().setVisible(False)

        # Add widgets to layout
        anomaly_layout.addWidget(self.anomaly_status)
        anomaly_layout.addWidget(button_container)
        anomaly_layout.addWidget(self.anomaly_table)

        # Processes tab
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget) 

        # Add Show All/Show Less button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignRight)  
        self.show_all_button = QPushButton("Show More")
        self.show_all_button.setMaximumWidth(130)
        self.show_all_button.setFixedHeight(30)         
        self.show_all_button.clicked.connect(self.toggle_process_view)
        self.show_all_processes = False
        button_layout.addWidget(self.show_all_button)
        processes_layout.addWidget(button_container)

        # Create table widget for processes
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(['Process Name', 'Status', 'CPU %', 'Memory %', 'Create Time'])
        
        # Set column stretching
        header = self.process_table.horizontalHeader()
        for i in range(self.process_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        header.setDefaultAlignment(Qt.AlignLeft)
        self.process_table.verticalHeader().setVisible(False)
        processes_layout.addWidget(self.process_table)
        #tabs.addTab(processes_widget, "Processes")        
        
        # Cpu details tab
        cpu_widget = QWidget()
        cpu_layout = QVBoxLayout(cpu_widget)  
        self.cpu_table = QTableWidget()
        cpu_metrics = [
            ("CPU Usage", "--"),
            ("CPU Frequency", "--"),
            ("Logical Core Count", "--"),
            ("Physical Core Count", "--"),
            ("CPU Load", "--"),
            ("Context Switches", "--"),
            ("Interrupts", "--"),
            ("System Calls", "--"),
            ("User Time", "--"),
            ("System Time", "--"),
            ("Idle Time", "--"),
            ("CPU Temperature", "--"),
        ]
        self.cpu_table.setRowCount(len(cpu_metrics))
        self.cpu_table.setColumnCount(2)
        self.cpu_table.setHorizontalHeaderLabels(["Metric", "Value"])  

        cpu_header = self.cpu_table.horizontalHeader()
        for i in range(self.cpu_table.columnCount()):
            cpu_header.setSectionResizeMode(i, QHeaderView.Stretch)

        for row, (metric_name, metric_value) in enumerate(cpu_metrics):
            self.cpu_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.cpu_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.cpu_table.verticalHeader().setVisible(False)
        self.cpu_table.horizontalHeader().setStretchLastSection(True)
        cpu_layout.addWidget(self.cpu_table)
        #tabs.addTab(cpu_widget, "CPU Details")

        # Memory details tab
        memory_widget = QWidget()
        memory_layout = QVBoxLayout(memory_widget)  
        self.memory_table = QTableWidget()
        self.memory_table.setRowCount(8)
        self.memory_table.setColumnCount(2)
        self.memory_table.setHorizontalHeaderLabels(["Metric", "Value"])  

        memory_header = self.memory_table.horizontalHeader()
        for i in range(self.memory_table.columnCount()):
            memory_header.setSectionResizeMode(i, QHeaderView.Stretch)

        # Populate the table with memory details
        memory_metrics = [
            ("Total Memory", "--"),
            ("Available Memory", "--"),
            ("Memory Usage", "--"),
            ("Used Memory", "--"),
            ("Swap Total", "--"),
            ("Swap Used", "--"),
            ("Swap Free", "--"),
            ("Swap Usage", "--"),
        ]

        for row, (metric_name, metric_value) in enumerate(memory_metrics):
            self.memory_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.memory_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.memory_table.verticalHeader().setVisible(False)
        self.memory_table.horizontalHeader().setStretchLastSection(True)
        memory_layout.addWidget(self.memory_table)

        # Disk tab setup
        disk_widget = QWidget()
        disk_layout = QVBoxLayout(disk_widget)
        self.disk_table = QTableWidget()
        disk_metrics = [
            ("Total Disk Space", "--"),
            ("Used Disk Space", "--"),
            ("Free Disk Space", "--"),
            ("Disk Usage", "--"),
            ("Read Count", "--"),
            ("Write Count", "--"),
            ("Read Bytes", "--"),
            ("Write Bytes", "--"),
            ("Read Time", "--"),
            ("Write Time", "--"),
        ]
        self.disk_table.setRowCount(len(disk_metrics))
        self.disk_table.setColumnCount(2)
        self.disk_table.setHorizontalHeaderLabels(["Metric", "Value"])

        disk_header = self.disk_table.horizontalHeader()
        for i in range(self.disk_table.columnCount()):
            disk_header.setSectionResizeMode(i, QHeaderView.Stretch)

        for row, (metric_name, metric_value) in enumerate(disk_metrics):
            self.disk_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.disk_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.horizontalHeader().setStretchLastSection(True)
        disk_layout.addWidget(self.disk_table)

        #Battery details tab
        battery_widget = QWidget()
        battery_layout = QVBoxLayout(battery_widget)
        self.battery_table = QTableWidget()
        self.battery_table.setRowCount(3)
        self.battery_table.setColumnCount(2)
        self.battery_table.setHorizontalHeaderLabels(["Metric", "Value"])        

        battery_header = self.battery_table.horizontalHeader()
        for i in range(self.battery_table.columnCount()):
            battery_header.setSectionResizeMode(i, QHeaderView.Stretch)

        battery_metrics = [
            ("Battery Percentage", "--"),
            ("Status", "--"),
            ("Total Time Remaining", "--"),
        ]        
        for row, (metric_name, metric_value) in enumerate(battery_metrics):
            self.battery_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.battery_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.battery_table.verticalHeader().setVisible(False)
        self.battery_table.horizontalHeader().setStretchLastSection(True)
        battery_layout.addWidget(self.battery_table)

        #Network details tab
        network_widget = QWidget()
        network_layout = QVBoxLayout(network_widget)    
        self.network_table = QTableWidget()
        self.network_table.setRowCount(4)
        self.network_table.setColumnCount(2)
        self.network_table.setHorizontalHeaderLabels(["Metric", "Value"])  

        network_header = self.network_table.horizontalHeader()
        for i in range(self.network_table.columnCount()):
            network_header.setSectionResizeMode(i, QHeaderView.Stretch)

        # Populate the table with network details
        network_metrics = [
            ("Upload Speed", "--"),
            ("Download Speed", "--"),
            ("Total Data Sent", "--"),
            ("Total Data Received", "--"),
        ]

        for row, (metric_name, metric_value) in enumerate(network_metrics):
            self.network_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.network_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.network_table.verticalHeader().setVisible(False)
        self.network_table.horizontalHeader().setStretchLastSection(True)
        network_layout.addWidget(self.network_table)
        #tabs.addTab(network_widget, "Network Details")    

        #Settings tab
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        
        #background running option
        background_group = QGroupBox("Background Running")
        background_layout = QVBoxLayout()
        self.background_checkbox = QCheckBox("Run in background")
        self.background_checkbox.setChecked(True)
        
        background_layout.addWidget(self.background_checkbox)
        background_group.setLayout(background_layout)
        
        #Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout()

        self.dark_button = QRadioButton("Dark Mode")
        self.dark_button.setChecked(True)        
        self.dark_button.toggled.connect(self.set_dark_mode)
        theme_layout.addWidget(self.dark_button)


        self.light_button = QRadioButton("Light Mode")
        self.light_button.toggled.connect(self.set_light_mode)
        theme_layout.addWidget(self.light_button)

        theme_group.setLayout(theme_layout)

        self.settings_layout.addWidget(background_group)
        self.settings_layout.addWidget(theme_group)
        self.settings_layout.addStretch()

        #read only
        self.process_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cpu_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.memory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.disk_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.network_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.battery_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # add all tabs and load set_dark_mode by default
        self.set_dark_mode()
        tabs.addTab(overview_widget, "Overview")
        tabs.addTab(cpu_widget, "CPU Details")
        tabs.addTab(memory_widget, "Memory Details")
        tabs.addTab(disk_widget, "Disk Details")
        tabs.addTab(network_widget, "Network Details")    
        tabs.addTab(anomaly_widget, "Anomaly Detection")
        tabs.addTab(battery_widget, "Battery Details")
        tabs.addTab(processes_widget, "Processes")
        tabs.addTab(self.settings_widget, "Settings")


    def toggle_process_view(self):
        self.show_all_processes = not self.show_all_processes
        self.show_all_button.setText("Show Less" if self.show_all_processes else "Show More")
        # Trigger table update with current data
        self.update_process_table(self.current_processes)

    def update_metrics(self, metrics):
        # Update labels
        self.memory_label.setText(f"Memory Usage: {metrics['memory']['percent']}%")
        self.disk_label.setText(f"Disk Usage: {metrics['disk']['percent']}%")
        self.network_label.setText(f"Network Usage: {metrics['network']['upload_speed']}kbps")
        self.cpu_percent.setText(f"CPU Usage: {metrics['cpu']['cpu_percent']}%")
        
        # Update graph data
        self.cpu_series.append(self.data_points, metrics['cpu']['cpu_percent'])
        self.memory_series.append(self.data_points, metrics['memory']['percent'])
        self.disk_series.append(self.data_points, metrics['disk']['percent'])
        self.network_series.append(self.data_points, metrics['network']['upload_speed'])    
        
        # Update CPU tab
        self.cpu_table.setItem(0, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_percent']}%"))
        self.cpu_table.setItem(1, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_freq']} MHz"))
        self.cpu_table.setItem(2, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_count_logical']}"))
        self.cpu_table.setItem(3, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_count_physical']}"))
        self.cpu_table.setItem(4, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_load_avg_1min']}"))
        self.cpu_table.setItem(5, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_context_switches']}"))
        self.cpu_table.setItem(6, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_interrupts']}"))
        self.cpu_table.setItem(7, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_syscalls']}"))
        self.cpu_table.setItem(8, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_user_time']}s"))
        self.cpu_table.setItem(9, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_system_time']}s"))
        self.cpu_table.setItem(10, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_idle_time']}s"))
        self.cpu_table.setItem(11, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_temp']}\u00B0C"))

        # Update memory tab
        self.memory_table.setItem(0, 1, QTableWidgetItem(f"{metrics['memory']['total'] / (1024**2)/ 1024:.2f} GB" if metrics['memory']['total'] / (1024**2) > 1024 else f"{metrics['memory']['total'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(1, 1, QTableWidgetItem(f"{(metrics['memory']['available'] / (1024**2)) / 1024:.2f} GB" if metrics['memory']['available'] / (1024**2) > 1024 else f"{metrics['memory']['available'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(2, 1, QTableWidgetItem(f"{metrics['memory']['percent']}%"))
        self.memory_table.setItem(3, 1, QTableWidgetItem(f"{(metrics['memory']['used'] / (1024**2)) / 1024:.2f} GB" if metrics['memory']['used'] / (1024**2) > 1024 else f"{metrics['memory']['used'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(4, 1, QTableWidgetItem(f"{metrics['memory']['swap_total'] / (1024**2) / 1024:.2f} GB" if metrics['memory']['swap_total'] / 1024 > 1 else f"{metrics['memory']['swap_total'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(5, 1, QTableWidgetItem(f"{metrics['memory']['swap_used'] / (1024**2) / 1024:.2f} GB" if metrics['memory']['swap_used'] / 1024 > 1 else f"{metrics['memory']['swap_used'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(6, 1, QTableWidgetItem(f"{metrics['memory']['swap_free'] / (1024**2) / 1024:.2f} GB" if metrics['memory']['swap_free'] / 1024 > 1 else f"{metrics['memory']['swap_free'] / (1024**2):.2f} MB"))
        self.memory_table.setItem(7, 1, QTableWidgetItem(f"{metrics['memory']['swap_percent']}%"))

        # Update disk tab
        self.disk_table.setItem(0, 1, QTableWidgetItem(f"{metrics['disk']['total'] / (1024**2):.2f} MB" if metrics['disk']['total'] / (1024**2) <= 1024 else f"{metrics['disk']['total'] / (1024**2) / 1024:.2f} GB" if metrics['disk']['total'] / (1024**2) <= 1024**2 else f"{metrics['disk']['total'] / (1024**2) / 1024**2:.2f} TB"))
        self.disk_table.setItem(1, 1, QTableWidgetItem(f"{metrics['disk']['used'] / (1024**2):.2f} MB" if metrics['disk']['used'] / (1024**2) <= 1024 else f"{metrics['disk']['used'] / (1024**2) / 1024:.2f} GB" if metrics['disk']['used'] / (1024**2) <= 1024**2 else f"{metrics['disk']['used'] / (1024**2) / 1024**2:.2f} TB"))
        self.disk_table.setItem(2, 1, QTableWidgetItem(f"{metrics['disk']['free'] / (1024**2):.2f} MB" if metrics['disk']['free'] / (1024**2) <= 1024 else f"{metrics['disk']['free'] / (1024**2) / 1024:.2f} GB" if metrics['disk']['free'] / (1024**2) <= 1024**2 else f"{metrics['disk']['free'] / (1024**2) / 1024**2:.2f} TB"))
        self.disk_table.setItem(3, 1, QTableWidgetItem(f"{metrics['disk']['percent']}%"))
        self.disk_table.setItem(4, 1, QTableWidgetItem(f"{metrics['disk']['read_count']}"))
        self.disk_table.setItem(5, 1, QTableWidgetItem(f"{metrics['disk']['write_count']}"))
        self.disk_table.setItem(6, 1, QTableWidgetItem(f"{metrics['disk']['read_bytes'] / (1024**2) / 1024:.2f} GB" if metrics['disk']['read_bytes'] / (1024**2) > 1024 else f"{metrics['disk']['read_bytes'] / (1024**2):.2f} MB"))
        self.disk_table.setItem(7, 1, QTableWidgetItem(f"{metrics['disk']['write_bytes'] / (1024**2) / 1024:.2f} GB" if metrics['disk']['write_bytes'] / (1024**2) > 1024 else f"{metrics['disk']['write_bytes'] / (1024**2):.2f} MB"))
        self.disk_table.setItem(8, 1, QTableWidgetItem(f"{metrics['disk']['read_time'] / 1000:.2f} sec" if metrics['disk']['read_time'] >= 60000 else f"{metrics['disk']['read_time'] / 60000:.2f} min" if metrics['disk']['read_time'] >= 3600000 else f"{metrics['disk']['read_time']:.2f} ms"))
        self.disk_table.setItem(9, 1, QTableWidgetItem(f"{metrics['disk']['write_time'] / 1000:.2f} sec" if metrics['disk']['write_time'] >= 60000 else f"{metrics['disk']['write_time'] / 60000:.2f} min" if metrics['disk']['write_time'] >= 3600000 else f"{metrics['disk']['write_time']:.2f} ms"))

        #update network tab
        self.network_table.setItem(0, 1, QTableWidgetItem(f"{metrics['network']['upload_speed'] / 1024:.2f} MB/s" if metrics['network']['upload_speed'] >= 1024 else f"{metrics['network']['upload_speed']} kb/s"))
        self.network_table.setItem(1, 1, QTableWidgetItem(f"{metrics['network']['download_speed'] / 1024:.2f} MB/s" if metrics['network']['download_speed'] >= 1024 else f"{metrics['network']['download_speed']} kb/s"))
        self.network_table.setItem(2, 1, QTableWidgetItem(f"{metrics['network']['total_data_sent'] / (1024**2):.2f} GB" if metrics['network']['total_data_sent'] >= 1024**2 else f"{metrics['network']['total_data_sent'] / 1024:.2f} MB" if metrics['network']['total_data_sent'] >= 1024 else f"{metrics['network']['total_data_sent']} kb"))
        self.network_table.setItem(3, 1, QTableWidgetItem(f"{metrics['network']['total_data_received'] / (1024**2):.2f} GB" if metrics['network']['total_data_received'] >= 1024**2 else f"{metrics['network']['total_data_received'] / 1024:.2f} MB" if metrics['network']['total_data_received'] >= 1024 else f"{metrics['network']['total_data_received']} kb"))

        #update battery tab
        self.battery_table.setItem(0, 1, QTableWidgetItem(f"{metrics['battery']['battery_percentage']}%"))
        self.battery_table.setItem(1, 1, QTableWidgetItem(f"{metrics['battery']['status']}"))
        self.battery_table.setItem(2, 1, QTableWidgetItem(f"{metrics['battery']['time_remaining']}"))

        if self.data_points > self.max_data_points:
            self.cpu_series.remove(0)
            self.memory_series.remove(0)
            self.disk_series.remove(0)
            self.network_series.remove(0)
            
            for chart in [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]:
                chart.axes(Qt.Horizontal)[0].setRange(self.data_points - self.max_data_points, self.data_points)
        self.data_points += 1

        #network
        if metrics['network']['upload_speed'] > self.max_network_value:
            self.max_network_value = metrics['network']['upload_speed']
    
        buffer = self.max_network_value * 0.1
        self.network_y.setRange(0, self.max_network_value + buffer)

    def update_process_table(self, processes):
        if not self.isVisible():
            return

        self.current_processes = processes
        self.process_table.setUpdatesEnabled(False)

        display_processes = processes if self.show_all_processes else [p for p in processes if p['cpu_percent'] > 0]
        self.process_table.setRowCount(len(display_processes))

        for row, process in enumerate(display_processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(process['name']))
            self.process_table.setItem(row, 1, QTableWidgetItem(f"{process['status']}"))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{process['cpu_percent']:.1f}"))
            self.process_table.setItem(row, 3, QTableWidgetItem(f"{process['memory_percent']:.1f}"))
            self.process_table.setItem(row, 4, QTableWidgetItem(f"{process['create_time']}"))

        self.process_table.setUpdatesEnabled(True)

    def on_detect_clicked(self):
        """Trigger anomaly detection and update table."""
        anomalies = detect_anomalies(OUTPUT_CSV, THRESHOLD_STEP)
        self.update_anomaly_table(anomalies)

    def update_anomaly_table(self, anomalies=None):
        """Update the anomaly detection table with results"""
        self.anomaly_table.setUpdatesEnabled(False)
        
        # Clear existing rows
        self.anomaly_table.setRowCount(0)
        
        if anomalies is not None and not anomalies.empty:
            # Update status label for anomaly
            self.anomaly_status.setText("⚠️ Anomalies Detected!")
            self.anomaly_status.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            
            # Update last run time
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_run_time.setText(f"Last Run: {current_time}")
            
            self.anomaly_table.setUpdatesEnabled(False)

            # Add rows for detected anomalies
            self.anomaly_table.setRowCount(len(anomalies))
            
            for row, anomaly in enumerate(anomalies.itertuples()):
                # Fill table with anomaly data
                self.anomaly_table.setItem(row, 0, QTableWidgetItem(f"{anomaly[1]:.2f}"))
                self.anomaly_table.setItem(row, 1, QTableWidgetItem(f"{anomaly[2]:.2f}"))
                self.anomaly_table.setItem(row, 2, QTableWidgetItem(f"{anomaly[3]:.2f}"))
                self.anomaly_table.setItem(row, 3, QTableWidgetItem(f"{anomaly[4]:.2f}"))
                self.anomaly_table.setItem(row, 4, QTableWidgetItem("⚠️ Anomaly"))
                
                # Set red color for anomaly rows
                for col in range(self.anomaly_table.columnCount()):
                    item = self.anomaly_table.item(row, col)
                    item.setForeground(QBrush(QColor(255, 0, 0)))
        else:
            # Show normal status
            self.anomaly_status.setText("System Status: Normal ✓")
            self.anomaly_status.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #2ecc71;
                    color: white;
                }
            """)
            # Update last run time
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_run_time.setText(f"Last Run: {current_time}")
            
            self.anomaly_table.setUpdatesEnabled(False)

        self.anomaly_table.setUpdatesEnabled(True)


    def closeEvent(self, event):
        if self.background_checkbox.isChecked():
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
        else:
            event.accept()
            sys.exit(0)    