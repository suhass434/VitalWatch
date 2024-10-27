STYLE_SHEET = """
QMainWindow {
    background-color: #2e2e2e;
}

QTabWidget::pane {
    border: 1px solid #3e3e3e;
    background: #2e2e2e;
}

QTabWidget::tab-bar {
    left: 5px;
}

QTabBar::tab {
    background: #3e3e3e;
    color: #ffffff;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background: #5e5e5e;
}

QPushButton {
    background-color: #4e4e4e;
    color: white;
    border: none;
    padding: 5px 15px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #5e5e5e;
}
"""