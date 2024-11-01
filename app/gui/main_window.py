from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPen
import threading
from app.gui.styles import STYLE_SHEET
import yaml
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_processes = []
        self.cpu_label = QLabel("CPU Usage: --")
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")
        self.network_label = QLabel("Network Usage: --")
        self.gpu_label = QLabel("GPU Usage: --")

        # Initialize data series for graphs
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.disk_series = QLineSeries()
        self.network_series = QLineSeries()
        self.gpu_series = QLineSeries()
        self.data_points = 0
        self.max_data_points = 50

        # Create charts
        self.cpu_chart = QChart()
        self.memory_chart = QChart()
        self.disk_chart = QChart()
        self.network_chart = QChart()
        self.gpu_chart = QChart()
        
        self.setup_charts()
        self.setup_ui()        

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
                'gpu_line': QColor("#FF6B6B")
                #'fill_color': QColor("#FF6B6B").lighter(170) 
            }       
        config = self.load_config()
        self.max_count = config['monitoring']['process']['max_count']

        # CPU Chart with enhanced styling
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

        #Gpu Usage Chart
        self.gpu_series.setColor(QColor("#FF6B6B"))
        self.gpu_chart.setBackgroundVisible(True)
        self.gpu_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.gpu_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.gpu_chart.addSeries(self.gpu_series)
        self.gpu_chart.setTitle("Gpu Usage %")
        self.gpu_chart.legend().hide()
        self.gpu_chart.setAnimationOptions(QChart.SeriesAnimations)

        gpu_x = QValueAxis()
        gpu_y = QValueAxis()
        gpu_x.setLabelsVisible(False)
        gpu_x.setLabelsColor(chart_theme['text'])
        gpu_y.setLabelsColor(chart_theme['text'])
        gpu_x.setGridLineColor(chart_theme['grid'])
        gpu_y.setGridLineColor(chart_theme['grid'])        
        gpu_x.setRange(0, self.max_data_points)
        gpu_y.setRange(0, 100)
        self.gpu_chart.addAxis(gpu_x, Qt.AlignBottom)
        self.gpu_chart.addAxis(gpu_y, Qt.AlignLeft)
        self.gpu_series.attachAxis(gpu_x)
        self.gpu_series.attachAxis(gpu_y)
        gpu_pen = QPen(chart_theme['gpu_line'])
        gpu_pen.setWidth(config['gui']['pen_thickness'])
        self.gpu_series.setPen(gpu_pen)        

    def setup_ui(self):
        self.setWindowTitle("AutoGuard")
        self.setMinimumSize(800, 600)
        
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
        overview_layout.addWidget(self.cpu_label, 0, 0)
        overview_layout.addWidget(QChartView(self.cpu_chart), 1, 0)
        overview_layout.addWidget(self.memory_label, 0, 1)
        overview_layout.addWidget(QChartView(self.memory_chart), 1, 1)
        overview_layout.addWidget(self.disk_label, 2, 0)
        overview_layout.addWidget(QChartView(self.disk_chart), 3, 0)
        overview_layout.addWidget(self.gpu_label, 2, 1)
        overview_layout.addWidget(QChartView(self.gpu_chart), 3, 1)        
        tabs.addTab(overview_widget, "Overview")

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
        tabs.addTab(processes_widget, "Processes")        


        #Settings tab
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        #background running option
        background_group = QGroupBox("Background Running")
        background_layout = QVBoxLayout()

        self.background_checkbox = QCheckBox("Run in background")
        self.background_checkbox.setChecked(True)

        background_layout.addWidget(self.background_checkbox)
        background_group.setLayout(background_layout)
        settings_layout.addWidget(background_group)
        settings_layout.addStretch()
    
        tabs.addTab(settings_widget, "Settings")


    def toggle_process_view(self):
        self.show_all_processes = not self.show_all_processes
        self.show_all_button.setText("Show Less" if self.show_all_processes else "Show More")
        # Trigger table update with current data
        self.update_process_table(self.current_processes)

    def update_metrics(self, metrics):
        # Update labels
        self.cpu_label.setText(f"CPU Usage: {metrics['cpu']['cpu_percent']}%")
        self.memory_label.setText(f"Memory Usage: {metrics['memory']['percent']}%")
        self.disk_label.setText(f"Disk Usage: {metrics['disk']['percent']}%")
        self.network_label.setText(f"Network Usage: {metrics['network']['upload_speed']}kb")
        
        # Update graph data
        self.cpu_series.append(self.data_points, metrics['cpu']['cpu_percent'])
        self.memory_series.append(self.data_points, metrics['memory']['percent'])
        self.disk_series.append(self.data_points, metrics['disk']['percent'])
        self.network_series.append(self.data_points, metrics['network']['upload_speed'])
        
        if self.data_points >= self.max_data_points:
            self.cpu_series.remove(0)
            self.memory_series.remove(0)
            self.disk_series.remove(0)
            self.network_series.remove(0)
            
            for chart in [self.cpu_chart, self.memory_chart, self.disk_chart, self.network_chart]:
                chart.axes(Qt.Horizontal)[0].setRange(self.data_points - self.max_data_points, self.data_points)
        self.data_points += 1

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