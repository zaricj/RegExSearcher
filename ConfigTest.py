from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
import os
import json

class ConfigHandler:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(script_dir, "_internal", "configuration")
        self.config_file = os.path.join(self.config_dir, "config.json")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_config()
        return self.get_default_config()

    def get_default_config(self):
        return {"theme": "light", "window_size": (800, 600)}

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

class MainWindow(QMainWindow):
    def __init__(self, config_handler):
        super().__init__()
        self.config_handler = config_handler
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PySide6 Config Example")
        self.resize(*self.config_handler.config.get("window_size", (800, 600)))

        layout = QVBoxLayout()
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)

        layout.addWidget(save_button)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def save_settings(self):
        # Example: Save current window size to the configuration
        self.config_handler.config["window_size"] = (self.width(), self.height())
        self.config_handler.save_config()

if __name__ == "__main__":
    app = QApplication([])
    config_handler = ConfigHandler()
    window = MainWindow(config_handler)
    window.show()
    app.exec()
