from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox, QButtonGroup, QRadioButton, QApplication)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
import threading
from app.gui.styles import STYLE_SHEET
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
        
        self.setup_charts()
        self.setup_ui()  

    def set_dark_mode(self):
        #self.setStyleSheet(STYLE_SHEET["dark"])
        self.cpu_chart.setBackgroundBrush(QBrush(QColor("#2B2B2B")))
        self.memory_chart.setBackgroundBrush(QBrush(QColor("#2B2B2B")))
        self.disk_chart.setBackgroundBrush(QBrush(QColor("#2B2B2B")))
        self.network_chart.setBackgroundBrush(QBrush(QColor("#2B2B2B")))
        self.cpu_percent.setStyleSheet("color: white")
        self.memory_label.setStyleSheet("color: white")
        self.disk_label.setStyleSheet("color: white")
        self.network_label.setStyleSheet("color: white")
        self.process_table.setStyleSheet("background-color: #2B2B2B; color: white")
        self.cpu_table.setStyleSheet("background-color: #2B2B2B; color: white")
        self.memory_table.setStyleSheet("background-color: #2B2B2B; color: white")
        self.disk_table.setStyleSheet("background-color: #2B2B2B; color: white")
        self.network_table.setStyleSheet("background-color: #2B2B2B; color: white")
        self.settings_widget.setStyleSheet("background-color: #2B2B2B;  color: white")

    def set_light_mode(self):
        #self.setStyleSheet(STYLE_SHEET["light"])
        self.cpu_chart.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.memory_chart.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.disk_chart.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.network_chart.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.cpu_percent.setStyleSheet("color: black")
        self.memory_label.setStyleSheet("color: black")
        self.disk_label.setStyleSheet("color: black")
        self.network_label.setStyleSheet("color: black")
        self.process_table.setStyleSheet("background-color: #FFFFFF; color: black")
        self.cpu_table.setStyleSheet("background-color: #FFFFFF; color: black")
        self.memory_table.setStyleSheet("background-color: #FFFFFF; color: black")
        self.disk_table.setStyleSheet("background-color: #FFFFFF; color: black")
        self.network_table.setStyleSheet("background-color: #FFFFFF; color: black")
        self.settings_widget.setStyleSheet("background-color: #FFFFFF; color: black")

    def load_config(self):
        with open('config/config.yaml', 'r') as file:
            return yaml.safe_load(file)    

    def setup_charts(self):
        chart_theme = {
                'background': QColor("#2B2B2B"),
                'text': QColor("#FFFFFF"),
                'grid': QColor("#3C3F41"),
                'cpu_line': QColor("#FF6B6B"),
                'memory_line': QColor("#FF6B6B"),#"#4ECDC4"
                'disk_line': QColor("#FF6B6B"),
                'network_line': QColor("#FF6B6B")
            }       
        config = self.load_config()
        self.max_count = config['monitoring']['process']['max_count']

        # CPU Chart
        self.cpu_series.setColor(chart_theme['cpu_line'])
        self.cpu_chart.addSeries(self.cpu_series)  
        self.cpu_chart.setBackgroundVisible(True)
        self.cpu_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.cpu_chart.setTitleBrush(QBrush(chart_theme['text']))
        self.cpu_chart.setTitle("CPU Usage %")
        self.cpu_chart.legend().hide()  # Hide legend for cleaner look
        self.cpu_chart.setAnimationOptions(QChart.SeriesAnimations)  # smooth animations
        
        axis_x = QValueAxis()
        axis_y = QValueAxis()
        axis_x.setLabelsVisible(False)
        axis_x.setLabelsColor(chart_theme['text'])
        axis_y.setLabelsColor(chart_theme['text'])
        axis_x.setGridLineColor(chart_theme['grid'])
        axis_y.setGridLineColor(chart_theme['grid'])
        axis_x.setRange(0, self.max_data_points)
        axis_y.setRange(0, 100)
        axis_y.setTickCount(6)  # More readable tick intervals
        self.cpu_chart.addAxis(axis_x, Qt.AlignBottom)
        self.cpu_chart.addAxis(axis_y, Qt.AlignLeft)
        self.cpu_series.attachAxis(axis_x)
        self.cpu_series.attachAxis(axis_y)
        cpu_pen = QPen(chart_theme['cpu_line'])
        cpu_pen.setWidth(config['gui']['pen_thickness'])
        self.cpu_series.setPen(cpu_pen)

        # Memory Chart - Create new axes instances
        self.memory_series.setColor(QColor("#FF6B6B"))
        self.memory_chart.setBackgroundVisible(True)
        self.memory_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.memory_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.memory_chart.addSeries(self.memory_series)
        self.memory_chart.setTitle("Memory Usage %")
        self.memory_chart.legend().hide()
        self.memory_chart.setAnimationOptions(QChart.SeriesAnimations)

        memory_x = QValueAxis()
        memory_y = QValueAxis()
        memory_x.setLabelsVisible(False)
        memory_x.setLabelsColor(chart_theme['text'])
        memory_y.setLabelsColor(chart_theme['text'])
        memory_x.setGridLineColor(chart_theme['grid'])
        memory_y.setGridLineColor(chart_theme['grid'])        
        memory_x.setRange(0, self.max_data_points)
        memory_y.setRange(0, 100)
        axis_y.setTickCount(6)
        self.memory_chart.addAxis(memory_x, Qt.AlignBottom)
        self.memory_chart.addAxis(memory_y, Qt.AlignLeft)
        self.memory_series.attachAxis(memory_x)
        self.memory_series.attachAxis(memory_y)
        memory_pen = QPen(chart_theme['memory_line'])
        memory_pen.setWidth(config['gui']['pen_thickness'])
        self.memory_series.setPen(memory_pen)

        # Disk Chart - Create new axes instances
        self.disk_series.setColor(QColor("#FF6B6B"))
        self.disk_chart.setBackgroundVisible(True)
        self.disk_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.disk_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.disk_chart.addSeries(self.disk_series)
        self.disk_chart.setTitle("Disk Usage %")
        self.disk_chart.legend().hide()
        self.disk_chart.setAnimationOptions(QChart.SeriesAnimations)

        disk_x = QValueAxis()
        disk_y = QValueAxis()
        disk_x.setLabelsVisible(False)
        disk_x.setLabelsColor(chart_theme['text'])
        disk_y.setLabelsColor(chart_theme['text'])
        disk_x.setGridLineColor(chart_theme['grid'])
        disk_y.setGridLineColor(chart_theme['grid'])        
        disk_x.setRange(0, self.max_data_points)
        disk_y.setRange(0, 100)
        self.disk_chart.addAxis(disk_x, Qt.AlignBottom)
        self.disk_chart.addAxis(disk_y, Qt.AlignLeft)
        self.disk_series.attachAxis(disk_x)
        self.disk_series.attachAxis(disk_y)
        disk_pen = QPen(chart_theme['disk_line'])
        disk_pen.setWidth(config['gui']['pen_thickness'])
        self.disk_series.setPen(disk_pen)

        #network Chart
        self.max_network_value = 100
        self.network_series.setColor(QColor("#FF6B6B"))
        self.network_chart.setBackgroundVisible(True)
        self.network_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.network_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.network_chart.addSeries(self.network_series)
        self.network_chart.setTitle("Network Usage Kbps")
        self.network_chart.legend().hide()
        self.network_chart.setAnimationOptions(QChart.SeriesAnimations)

        network_x = QValueAxis()
        self.network_y = QValueAxis()
        network_x.setLabelsVisible(False)
        network_x.setLabelsColor(chart_theme['text'])
        self.network_y.setLabelsColor(chart_theme['text'])
        network_x.setGridLineColor(chart_theme['grid'])
        self.network_y.setGridLineColor(chart_theme['grid'])        
        network_x.setRange(0, self.max_data_points)
        self.network_y.setRange(0, self.max_network_value)
        self.network_chart.addAxis(network_x, Qt.AlignBottom)
        self.network_chart.addAxis(self.network_y, Qt.AlignLeft)
        self.network_series.attachAxis(network_x)
        self.network_series.attachAxis(self.network_y)
        network_pen = QPen(chart_theme['network_line'])
        network_pen.setWidth(config['gui']['pen_thickness'])
        self.network_series.setPen(network_pen)        

    def setup_ui(self): 
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

        self.light_button = QRadioButton("Light Mode")
        self.light_button.toggled.connect(self.set_light_mode)
        theme_layout.addWidget(self.light_button)

        self.dark_button = QRadioButton("Dark Mode")
        self.dark_button.setChecked(True)        
        self.dark_button.toggled.connect(self.set_dark_mode)
        theme_layout.addWidget(self.dark_button)

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