import os
import re
import csv
import sys
import json
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QListWidget, QLabel, QFileDialog, 
                               QTextEdit, QMenuBar, QMenu, QFrame, QMessageBox, QProgressBar, QStatusBar, QComboBox, QDialog)
from PySide6.QtGui import QAction, QIcon, QCloseEvent
from PySide6.QtCore import Qt, QFile, QTextStream, QObject, Signal, QThread, QSettings
from win32api import GetSystemMetrics
from _internal.modules.regex_generator import RegexGenerator

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(SCRIPT_DIR)

class ConfigHandler:
    def __init__(self):
        self.config_file = os.path.join(SCRIPT_DIR, "_internal","configuration","program_config.json")
        self.make_conf_dir_if_not_exist()
        self.config = self.load_config()
        
    def make_conf_dir_if_not_exist(self):
        if not os.path.exists(os.path.join(SCRIPT_DIR, "_internal", "configuration")):
            os.makedirs(os.path.join(SCRIPT_DIR, "_internal","configuration"), exist_ok=True)

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Warning", f"Warning: {self.config_file} is empty or contains invalid JSON. Using default configuration.")
                return self.get_default_config()

    def get_default_config(self):
        return {"default_key": {}, "default_key_other": {}}

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
            
class Worker(QObject):
    """
    Worker class that will run in a separate thread.
    This is a blueprint for implementing any long-running task.
    """
    
    progress = Signal(int)    # Signal for progress updates
    finished = Signal()       # Signal when task is complete
    output_set_text = Signal(str)
    output_append = Signal(str)
    
    def __init__(self, file_input, headers_input, pattern_list, output_window):
        super().__init__()
        self.file_input = file_input
        self.headers_input = headers_input
        self.pattern_list = pattern_list
        self.output_window = output_window
        self._is_running = True
    
    def stop(self):
        """Method to stop the running task"""
        self._is_running = False
    
    def run(self):
        """
        The actual task that will run in the thread.
        Main entry point when the thread starts.
        """
        try:
            self.search_and_save()
        except Exception as e:
            self.output_append.emit(f"Exception in worker thread: {str(e)}")
        finally:
            self.finished.emit()
        
    def regex_search(self, text, patterns):
        return {pattern: re.findall(pattern, text) for pattern in patterns}
    
    # Main Method for Searching and Saving the RegEx pattern results to CSV
    def search_and_save(self):
        try:
            file_path = self.file_input.text()
            headers = self.headers_input.text().split(",")
            patterns = [self.pattern_list.item(i).text() for i in range(self.pattern_list.count())]

            # Check if task should continue:
            if not self._is_running:
                self.output_append.emit("Task aborted successfully.")
                return
            
            if not file_path:
                self.output_append.emit("Error: Please select a log file.")
                return

            if len(headers) != len(patterns):
                self.output_append.emit("Error: Number of headers must match number of RegEx patterns")
                return

            try:
                self.output_set_text.emit("Started processing...")
                with open(file_path, "r") as file:
                    text = file.read()
            except Exception as e:
                self.output_append.emit(f"Error: {e}")
                return
            
            # Check if task should continue:
            if not self._is_running:
                self.output_append.emit("Task aborted successfully.")
                return

            results = self.regex_search(text, patterns)
            csv_data = list(zip(*results.values()))

            today_date = datetime.now()
            formatted_today_date = today_date.strftime("%d.%m.%y-%H%M%S")
            
            # Check if task should continue:
            if not self._is_running:
                self.output_append.emit("Task aborted successfully.")
                return
            
            try:
                os.makedirs("CSVResults", exist_ok=True)
                with open(f"CSVResults/regex_matches_{formatted_today_date}.csv", mode="w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                    for index, row in enumerate(csv_data, 1):
                        self.progress.emit((index + 1) / len(csv_data) * 100)
                    writer.writerows(csv_data)
                        
                self.output_append.emit(f"Matches saved to 'CSVResults\\regex_matches_{formatted_today_date}.csv'")
            except Exception as e:
                self.output_set_text.emit(f"Error: {e}")
        except Exception as ex:
            self.output_set_text.emit(f"An exception occurred in method search_and_save: {str(ex)}")
        
        finally:
            file.close()
            self.finished.emit()

class SettingsWindow(QDialog):
    """
    This "Settings Window" is a QDialog. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store reference to parent window
        self.current_theme = os.path.join(SCRIPT_DIR, "_internal", "themes", "dark_theme.qss")
        self.initialize_theme(self.current_theme)
        
        main_layout = QVBoxLayout()
        hor_layout_theme = QHBoxLayout()
        
        # Standalone Widgets
        self.save_and_close_button = QPushButton("Save and Close")
        
        # Widgets for the theme settings
        self.apply_theme_button = QPushButton("Apply Theme")
        self.apply_theme_button.clicked.connect(self.apply_theme)
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["Dark", "Light"])
        
        # Add theme widgets to the layout
        hor_layout_theme.addWidget(QLabel("Change Theme:"))
        hor_layout_theme.addWidget(self.theme_combobox)
        hor_layout_theme.addWidget(self.apply_theme_button)
        
        main_layout.addLayout(hor_layout_theme)
        main_layout.addWidget(self.save_and_close_button)
        self.setLayout(main_layout)
    
    def apply_theme(self):
        selected_theme = self.theme_combobox.currentText()
        theme_file = os.path.join(
            SCRIPT_DIR, 
            "_internal",
            "themes",
            "dark_theme.qss" if selected_theme == "Dark" else "light_theme.qss"
        )
        
        # Apply theme to both windows
        if self.parent:
            self.parent.initialize_theme(theme_file)
        self.initialize_theme(theme_file)
    
    def initialize_theme(self, theme_file):
        try:
            file = QFile(theme_file)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                self.setStyleSheet(stylesheet)
            file.close()
        except Exception as ex:
            QMessageBox.critical(self, "Theme load error", f"Failed to load theme: {str(ex)}")

class RegExSearcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.icon = QIcon("_internal/icon/lobster_logo.ico")
        self.current_theme = os.path.join(SCRIPT_DIR, "_internal", "themes", "dark_theme.qss")  # Sets the global main theme from the file
        self.regex_thread = None
        self.regex_worker = None
        
        # Initialize UI first
        self.setWindowTitle("Lobster Log Searcher")
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowIcon(self.icon)
        self.init_ui()
        
        # Create settings window after UI initialization
        self.settings_window = SettingsWindow(parent=self)  # Pass self as parent
        
        # Initialize theme last
        self.initialize_theme(self.current_theme)
        
        # Settings to save current location of the windows on exit
        self.settings = QSettings("Application", "Name")
        geometry = self.settings.value("geometry", bytes())
        self.restoreGeometry(geometry)
        self.create_menu_bar()
        
    def initialize_theme(self, theme_file):
        try:
            file = QFile(theme_file)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                self.setStyleSheet(stylesheet)
            file.close()
        except Exception as ex:
            QMessageBox.critical(self, "Theme load error", f"Failed to load theme: {str(ex)}")
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # ====================================== Start Menu Bar Start ====================================== #

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        test_logs_action = QAction("Lobster TEST Logs Folder", self)
        test_logs_action.triggered.connect(lambda: self.set_logs_folder("//nesist02/hub/logs/DataWizard"))
        file_menu.addAction(test_logs_action)

        prod_logs_action = QAction("Lobster PROD Logs Folder", self)
        prod_logs_action.triggered.connect(lambda: self.set_logs_folder("//nesis002/hub/logs/DataWizard"))
        file_menu.addAction(prod_logs_action)

        file_menu.addSeparator()

        clear_output_action = QAction("Clear Output", self)
        clear_output_action.triggered.connect(self.clear_output)
        file_menu.addAction(clear_output_action)
        
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Open Menu
        open_menu = menubar.addMenu("&Open")
        
        open_csv_folder = QAction("Open CSV Results Folder...", self)
        open_csv_folder.triggered.connect(lambda: self.open_folder_helper_method(os.path.join(SCRIPT_DIR, "CSVResults")))
        open_menu.addAction(open_csv_folder)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        how_to_use_action = QAction("How to Use", self)
        help_menu.addAction(how_to_use_action)

        # Expressions menu
        expressions_menu = menubar.addMenu("&Expressions")
        
        time_pattern_action = QAction("Time Pattern", self)
        time_pattern_action.triggered.connect(lambda: self.set_pattern(r"\b(\d{2}:\d{2}:\d{2})\b", "Time"))
        expressions_menu.addAction(time_pattern_action)

        job_number_action = QAction("Job Number Pattern", self)
        job_number_action.triggered.connect(lambda: self.set_pattern(r"Job:\s+((?:\d+|GENERAL))", "Job number"))
        expressions_menu.addAction(job_number_action)

        profilename_action = QAction("Profilename Pattern", self)
        profilename_action.triggered.connect(lambda: self.set_pattern(r"\[(.*?)]", "Profile name"))
        expressions_menu.addAction(profilename_action)

        filename_action = QAction("Filename Pattern", self)
        filename_action.triggered.connect(lambda: self.set_pattern(r"Start processing data of file '(.*?)'", "filename"))
        expressions_menu.addAction(filename_action)

        filesize_action = QAction("Filesize Pattern", self)
        filesize_action.triggered.connect(lambda: self.set_pattern(r"length=(\d+),", "Filesize in bytes"))
        expressions_menu.addAction(filesize_action)

    # ====================================== End Menu Bar End ====================================== #
    
    
    # ====================================== Start Initialize UI Start ====================================== #
    
    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # RegEx builder from string(s)
        regex_builder_layout = QHBoxLayout()
        self.build_input = QLineEdit()
        self.build_input.setPlaceholderText("Enter string to generate regex from...")
        generate_button = QPushButton("Generate")
        generate_button.setMinimumWidth(80)
        generate_button.clicked.connect(self.generate_regex)
        
        regex_builder_layout.addWidget(self.build_input)
        regex_builder_layout.addWidget(generate_button)

        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a log file...")
        file_button = QPushButton("Browse")
        file_button.setMinimumWidth(80)
        file_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(file_button)

        # RegEx pattern input
        pattern_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter RegEx pattern...")
        add_button = QPushButton("Add")
        add_button.setMinimumWidth(80)
        add_button.clicked.connect(self.add_pattern)
        pattern_layout.addWidget(self.pattern_input)
        pattern_layout.addWidget(add_button)

        # Pattern list
        self.pattern_list = QListWidget()
        self.pattern_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pattern_list.customContextMenuRequested.connect(self.show_context_menu)

        # Headers input
        self.headers_input = QLineEdit()
        self.headers_input.setClearButtonEnabled(True)

        # Statusbar layout
        statusbar_layout = QHBoxLayout()
        
        # Search button
        self.search_button = QPushButton("Search and Save to CSV")
        self.search_button.clicked.connect(self.start_regex_and_save)
        self.stop_search_button = QPushButton("Abort Task")
        self.stop_search_button.setDisabled(True)
        self.stop_search_button.setHidden(True)
        self.stop_search_button.clicked.connect(self.stop_search_and_save)
        # CSV results output path statusbar
        self.csv_results_statusbar = QStatusBar()
        self.csv_results_statusbar.setSizeGripEnabled(False)
        self.csv_results_statusbar.showMessage(os.path.join(SCRIPT_DIR, "CSVResults"))
        self.csv_results_statusbar.setStyleSheet("font-size: 12px; color: #ffffff;")
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(lambda: self.open_folder_helper_method(os.path.join(SCRIPT_DIR, "CSVResults")))
        # Add it to the statusbar layout
        statusbar_layout.addWidget(self.csv_results_statusbar)
        statusbar_layout.addWidget(self.open_button)
        
        refresh_theme_button = QPushButton("Refresh Theme")
        refresh_theme_button.clicked.connect(self.refresh_theme)

        # Output window
        self.output_window = QTextEdit()
        self.output_window.setReadOnly(True)
        
        # Progressbar
        self.progress_bar = QProgressBar()

        # Add widgets to layouts
        left_layout.addLayout(file_layout)
        left_layout.addLayout(regex_builder_layout)
        left_layout.addLayout(pattern_layout)
        left_layout.addWidget(self.pattern_list)
        left_layout.addWidget(QLabel("Enter CSV Headers (comma separated):"))
        left_layout.addWidget(self.headers_input)
        left_layout.addWidget(self.search_button)
        left_layout.addWidget(self.stop_search_button)
        left_layout.addWidget(refresh_theme_button)
        left_layout.addLayout(statusbar_layout)

        right_layout.addWidget(self.output_window)
        right_layout.addWidget(self.progress_bar)

        # Add layouts to main layout
        main_layout.addLayout(left_layout)
        main_layout.addWidget(QFrame(frameShape=QFrame.VLine))
        main_layout.addLayout(right_layout)

        # Set main widget layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
    def closeEvent(self, event):
        geometry = self.saveGeometry()
        self.settings.setValue("geometry", geometry)
        super(RegExSearcher, self).closeEvent(event)
        
    # ====================================== End Initialize UI End ====================================== #
    
    def generate_regex(self):
        input_element = self.build_input.text()
        if len(input_element) > 0:
            self.generator = RegexGenerator(self.build_input.text())
            self.pattern_input.setText(self.generator.get_regex())
            self.output_window.setText(f"Generated the following RegEx: '{self.generator.get_regex()}'.\nPress 'Add' to add it to the list")
        else:
            QMessageBox.warning(self, "Input warning", "No string has been entered in the input element.")
    
    def refresh_theme(self):
        try:
            self.initialize_theme(self.current_theme)
        except Exception as ex:
            self.output_window.setText(f"An exception occurred: {str(ex)}")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "", "Log File (*.log)")
        if file_path:
            self.file_input.setText(file_path)

    def add_pattern(self):
        pattern = self.pattern_input.text()
        if pattern:
            self.pattern_list.addItem(pattern)
            self.pattern_input.clear()

    def show_context_menu(self, position):
        context_menu = QMenu()
        delete_action = context_menu.addAction("Delete")
        delete_all_action = context_menu.addAction("Delete All")

        action = context_menu.exec(self.pattern_list.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_pattern()
        elif action == delete_all_action:
            self.delete_all_patterns()

    def delete_selected_pattern(self):
        for item in self.pattern_list.selectedItems():
            self.pattern_list.takeItem(self.pattern_list.row(item))

    def delete_all_patterns(self):
        self.pattern_list.clear()

    def set_logs_folder(self, folder_path):
        self.file_input.setText(folder_path)

    def clear_output(self):
        self.output_window.clear()
        
    def open_folder_helper_method(self, folder_path):
        try:
            if not os.path.isdir(folder_path) and os.path.exists(folder_path):
                QMessageBox.critical(self,"Not a valid path",f"The entered folder path '{folder_path}' is not valid or does not exist.")
            else:
                os.startfile(folder_path)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(self, "Error", message)

    def set_pattern(self, pattern, header):
        self.pattern_input.setText(pattern)
        current_headers = self.headers_input.text()
        if current_headers:
            self.headers_input.setText(f"{current_headers},{header}")
        else:
            self.headers_input.setText(header)
        self.add_pattern()
    
    def open_settings(self):
        width, height = GetSystemMetrics(0) / 2, GetSystemMetrics(1) / 2
        self.settings_window.setWindowTitle("Lobster Log Searcher - Settings")
        self.settings_window.setWindowIcon(self.icon)
        self.settings_window.setGeometry(width , height, 800, 400 )
        self.settings_window.show()
            

    # ======================== RegExSearch and Save Methods ======================== #
    
    def start_regex_and_save(self):
        self.regex_thread = QThread()
        self.regex_worker = Worker(self.file_input, self.headers_input, self.pattern_list, self.output_window)
        self.regex_worker.moveToThread(self.regex_thread)
        
        # Connect Signals
        self.regex_thread.started.connect(self.regex_worker.run)
        self.regex_worker.output_set_text.connect(self.output_window.setText)
        self.regex_worker.output_append.connect(self.output_window.append)
        self.regex_worker.finished.connect(self.regex_thread.quit)
        self.regex_worker.finished.connect(self.on_finished_search_and_save)
        self.regex_worker.progress.connect(self.update_progress)
        
        # Update the UI buttons
        self.stop_search_button.setDisabled(False)
        self.stop_search_button.setHidden(False)
        self.search_button.setDisabled(True)
        
        # Start the Thread
        self.regex_thread.start()
        
    def stop_search_and_save(self):
        if hasattr(self, "regex_worker"):
            self.regex_worker.stop()
            self.output_window.setText("Aborting task, please wait...")
            
    def on_finished_search_and_save(self):
        self.stop_search_button.setDisabled(True)
        self.stop_search_button.setHidden(True)
        self.search_button.setDisabled(False)
        self.progress_bar.reset()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegExSearcher()
    window.show()
    app.exec()
