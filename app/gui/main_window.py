from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QCheckBox, QButtonGroup, QRadioButton, QApplication, QGraphicsRectItem, QGraphicsDropShadowEffect)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
import threading
#from app.gui.styles import STYLE_SHEET
from app.gui.styleSheet import STYLE_SHEET
import yaml
import sys

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
        self.cpu_temp_label = QLabel("--")
        self.current_processes = []
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")
        self.network_label = QLabel("Network Usage: --")

        # Initialize data series for graphs
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.disk_series = QLineSeries()
        self.network_series = QLineSeries()
        self.cpu_temp_series = QLineSeries()
        self.data_points = 0
        self.max_data_points = 50

        # Create charts
        self.cpu_chart = QChart()
        self.memory_chart = QChart()
        self.disk_chart = QChart()
        self.network_chart = QChart()
        self.cpu_temp_chart = QChart()
        
        self.setup_ui()  

    def set_theme(self, mode='dark'):
        """
        Set the application theme to either dark or light mode
        Args:
            mode (str): 'dark' or 'light'
        """
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
            
            # Update series colors
            for series in chart.series():
                pen = QPen(QColor(colors["line"]))
                pen.setWidth(self.load_config()['gui']['pen_thickness'])
                series.setPen(pen)
        
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
        
        # Tables styling
        tables = [
            self.process_table, self.cpu_table, self.memory_table, 
            self.disk_table, self.network_table
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
            
            QPushButton {{
                background-color: {colors['background_color']};
                color: {colors['text_color']};
                border: 1px solid {colors['border_color']};
                padding: 5px 10px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['grid_color']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['chart_grid']};
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
        
        return axis_y


    def setup_ui(self):
        config = self.load_config()
        self.max_count = config['monitoring']['process']['max_count']

        self.setWindowTitle("AutoGuard")
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
        self.setup_chart(self.cpu_chart, self.cpu_series, "CPU Usage %", y_axis_max=100)
        self.setup_chart(self.memory_chart, self.memory_series, "Memory Usage %", y_axis_max=100)
        self.setup_chart(self.disk_chart, self.disk_series, "Disk Usage %", y_axis_max=100)
    
        self.max_network_value = 100
        self.network_y = self.setup_chart(self.network_chart, self.network_series, "Network Usage Kbps", y_axis_max=self.max_network_value)

        # Add labels to overview tab
        overview_layout.addWidget(self.cpu_percent, 0, 0)
        overview_layout.addWidget(QChartView(self.cpu_chart), 1, 0)
        overview_layout.addWidget(self.memory_label, 0, 1)
        overview_layout.addWidget(QChartView(self.memory_chart), 1, 1)
        overview_layout.addWidget(self.disk_label, 2, 0)
        overview_layout.addWidget(QChartView(self.disk_chart), 3, 0)        
        overview_layout.addWidget(self.network_label, 2, 1)
        overview_layout.addWidget(QChartView(self.network_chart), 3, 1)        
        #tabs.addTab(overview_widget, "Overview")

        # Processes tab
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget) 

        # Add Show All/Show Less button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignRight)  
        self.show_all_button = QPushButton("Show More")
        self.show_all_button.setMaximumWidth(130)  # Set maximum width
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
        self.cpu_table.setRowCount(10)
        self.cpu_table.setColumnCount(2)
        self.cpu_table.setHorizontalHeaderLabels(["Metric", "Value"])  

        cpu_header = self.cpu_table.horizontalHeader()
        for i in range(self.cpu_table.columnCount()):
            cpu_header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        # Populate the table with CPU details
        cpu_metrics = [
            ("CPU Usage", "--"),
            ("CPU Temperature", "--"),
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
        ]

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
        #tabs.addTab(memory_widget, "Memory Details")

        # Disk tab setup
        disk_widget = QWidget()
        disk_layout = QVBoxLayout(disk_widget)
        self.disk_table = QTableWidget()
        self.disk_table.setRowCount(10)  # Adjust rows as needed based on metrics
        self.disk_table.setColumnCount(2)
        self.disk_table.setHorizontalHeaderLabels(["Metric", "Value"])

        disk_header = self.disk_table.horizontalHeader()
        for i in range(self.disk_table.columnCount()):
            disk_header.setSectionResizeMode(i, QHeaderView.Stretch)

        # Populate the table with disk metrics
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

        for row, (metric_name, metric_value) in enumerate(disk_metrics):
            self.disk_table.setItem(row, 0, QTableWidgetItem(metric_name))
            self.disk_table.setItem(row, 1, QTableWidgetItem(str(metric_value)))

        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.horizontalHeader().setStretchLastSection(True)
        disk_layout.addWidget(self.disk_table)
        #tabs.addTab(disk_widget, "Disk Details")

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
            ("Upload Speed", "--"),  # in kb per second
            ("Download Speed", "--"),  # in kb per second
            ("Total Data Sent", "--"),  # total kb sent
            ("Total Data Received", "--"),  # total kb received
            # ("Packets Sent", "--"),
            # ("Packets Received", "--"),
            # ("Errors Sent", "--"),
            # ("Errors Received", "--"),
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
        
        # add all tabs and load set_dark_mode by default
        self.set_dark_mode()
        tabs.addTab(overview_widget, "Overview")
        tabs.addTab(cpu_widget, "CPU Details")
        tabs.addTab(memory_widget, "Memory Details")
        tabs.addTab(disk_widget, "Disk Details")
        tabs.addTab(network_widget, "Network Details")    
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
        self.cpu_temp_label.setText(f"CPU Temperature: {metrics['cpu']['cpu_temp']}\u00B0C")

        # Update graph data
        self.cpu_series.append(self.data_points, metrics['cpu']['cpu_percent'])
        self.memory_series.append(self.data_points, metrics['memory']['percent'])
        self.disk_series.append(self.data_points, metrics['disk']['percent'])
        self.network_series.append(self.data_points, metrics['network']['upload_speed'])
        self.cpu_temp_series.append(self.data_points, metrics['cpu_load']['cpu_temp'])

        # Update cpu tab
        self.cpu_table.setItem(0, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_percent']}%"))
        self.cpu_table.setItem(1, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_temp']}\u00B0C"))
        self.cpu_table.setItem(2, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_freq']} MHz"))
        self.cpu_table.setItem(3, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_count_logical']}"))
        self.cpu_table.setItem(4, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_count_physical']}"))
        self.cpu_table.setItem(5, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_load_avg_1min']}"))
        self.cpu_table.setItem(6, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_context_switches']}"))
        self.cpu_table.setItem(7, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_interrupts']}"))
        self.cpu_table.setItem(8, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_syscalls']}"))
        self.cpu_table.setItem(9, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_user_time']}s"))
        self.cpu_table.setItem(10, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_system_time']}s"))
        self.cpu_table.setItem(11, 1, QTableWidgetItem(f"{metrics['cpu']['cpu_idle_time']}s"))

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
        # self.network_table.setItem(4, 1, QTableWidgetItem(f"{metrics['network']['packets_sent']}"))
        # self.network_table.setItem(5, 1, QTableWidgetItem(f"{metrics['network']['packets_received']}"))
        # self.network_table.setItem(6, 1, QTableWidgetItem(f"{metrics['network']['errors_sent']}"))
        # self.network_table.setItem(7, 1, QTableWidgetItem(f"{metrics['network']['errors_received']}"))

        if self.data_points > self.max_data_points:
            self.cpu_series.remove(0)
            self.memory_series.remove(0)
            self.disk_series.remove(0)
            self.network_series.remove(0)
            self.cpu_temp_series.remove(0)
            
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
        sorted_processes = sorted(processes, key=lambda x: float(x['cpu_percent']), reverse=True)
        if self.show_all_processes:

            display_processes = sorted_processes[:100]
        else:
            display_processes = [p for p in sorted_processes if float(p['cpu_percent']) > 0]
        self.process_table.setUpdatesEnabled(True)   

        # Update table        
        self.process_table.setRowCount(len(display_processes))
        for row, process in enumerate(display_processes):
            self.process_table.setItem(row, 0, QTableWidgetItem(process['name']))
            self.process_table.setItem(row, 1, QTableWidgetItem(f"{process['status']}"))
            self.process_table.setItem(row, 2, QTableWidgetItem(f"{process['cpu_percent']:.1f}"))
            self.process_table.setItem(row, 3, QTableWidgetItem(f"{process['memory_percent']:.1f}"))        
            self.process_table.setItem(row, 4, QTableWidgetItem(f"{process['create_time']}"))


    def closeEvent(self, event):
        if self.background_checkbox.isChecked():
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
        else:
            event.accept()
            sys.exit(0)    