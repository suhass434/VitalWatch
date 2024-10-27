from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,QGridLayout, QTabWidget, QPushButton, QLabel)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import threading
from app.gui.styles import STYLE_SHEET

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cpu_label = QLabel("CPU Usage: --")
        self.memory_label = QLabel("Memory Usage: --")
        self.disk_label = QLabel("Disk Usage: --")

        # Initialize data series for graphs
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.disk_series = QLineSeries()
        self.data_points = 0
        self.max_data_points = 50

        # Create charts
        self.cpu_chart = QChart()
        self.memory_chart = QChart()
        self.disk_chart = QChart()
        
        self.setup_charts()
        self.setup_ui()        

    def setup_charts(self):
        chart_theme = {
        'background': QColor("#2B2B2B"),
        'text': QColor("#FFFFFF"),
        'grid': QColor("#3C3F41")
        }    
        
        # CPU Chart
        self.cpu_series.setColor(QColor("#FF6B6B"))
        self.cpu_chart.setBackgroundVisible(True)
        self.cpu_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.cpu_chart.setTitleBrush(QBrush(chart_theme['text']))
        self.cpu_chart.addSeries(self.cpu_series)
        self.cpu_chart.setTitle("CPU Usage %")
        axis_x = QValueAxis()
        axis_y = QValueAxis()
        axis_x.setLabelsColor(chart_theme['text'])
        axis_y.setLabelsColor(chart_theme['text'])
        axis_x.setGridLineColor(chart_theme['grid'])
        axis_y.setGridLineColor(chart_theme['grid'])
        axis_x.setRange(0, self.max_data_points)
        axis_y.setRange(0, 100)
        self.cpu_chart.addAxis(axis_x, Qt.AlignBottom)
        self.cpu_chart.addAxis(axis_y, Qt.AlignLeft)
        self.cpu_series.attachAxis(axis_x)
        self.cpu_series.attachAxis(axis_y)

        # Memory Chart - Create new axes instances
        self.memory_series.setColor(QColor("#FF6B6B"))
        self.memory_chart.setBackgroundVisible(True)
        self.memory_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.memory_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.memory_chart.addSeries(self.memory_series)
        self.memory_chart.setTitle("Memory Usage %")
        memory_x = QValueAxis()
        memory_y = QValueAxis()
        memory_x.setLabelsColor(chart_theme['text'])
        memory_y.setLabelsColor(chart_theme['text'])
        memory_x.setGridLineColor(chart_theme['grid'])
        memory_y.setGridLineColor(chart_theme['grid'])        
        memory_x.setRange(0, self.max_data_points)
        memory_y.setRange(0, 100)
        self.memory_chart.addAxis(memory_x, Qt.AlignBottom)
        self.memory_chart.addAxis(memory_y, Qt.AlignLeft)
        self.memory_series.attachAxis(memory_x)
        self.memory_series.attachAxis(memory_y)

        # Disk Chart - Create new axes instances
        self.disk_series.setColor(QColor("#FF6B6B"))
        self.disk_chart.setBackgroundVisible(True)
        self.disk_chart.setBackgroundBrush(QBrush(chart_theme['background']))
        self.disk_chart.setTitleBrush(QBrush(chart_theme['text']))    
        self.disk_chart.addSeries(self.disk_series)
        self.disk_chart.setTitle("Disk Usage %")
        disk_x = QValueAxis()
        disk_y = QValueAxis()
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
        
        # Processes tab
        processes_widget = QWidget()
        processes_layout = QGridLayout(processes_widget)

        # Add labels to Processes tab
        processes_layout.addWidget(self.cpu_label, 0, 0)
        processes_layout.addWidget(QChartView(self.cpu_chart), 1, 0)
        processes_layout.addWidget(self.memory_label, 0, 1)
        processes_layout.addWidget(QChartView(self.memory_chart), 1, 1)
        processes_layout.addWidget(self.disk_label, 2, 0)
        processes_layout.addWidget(QChartView(self.disk_chart), 3, 0)        
        tabs.addTab(processes_widget, "Processes")


        # Settings tab
        settings_widget = QWidget()
        tabs.addTab(settings_widget, "Settings")

    def update_metrics(self, metrics):
        # Update labels
        self.cpu_label.setText(f"CPU Usage: {metrics['cpu']['cpu_percent']}%")
        self.memory_label.setText(f"Memory Usage: {metrics['memory']['percent']}%")
        self.disk_label.setText(f"Disk Usage: {metrics['disk']['percent']}%")
        
        # Update graph data
        self.cpu_series.append(self.data_points, metrics['cpu']['cpu_percent'])
        self.memory_series.append(self.data_points, metrics['memory']['percent'])
        self.disk_series.append(self.data_points, metrics['disk']['percent'])

        if self.data_points > self.max_data_points:
            self.cpu_series.remove(0)
            self.memory_series.remove(0)
            self.disk_series.remove(0)

        self.data_points += 1

    def closeEvent(self, event):
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()