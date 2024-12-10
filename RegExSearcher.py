import os
import re
import csv
import sys
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QListWidget, QLabel, QFileDialog, 
                               QTextEdit, QMenuBar, QMenu, QFrame, QMessageBox, QProgressBar)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, QFile, QTextStream, QObject, Signal, QThread, QSettings
from _internal.modules.regex_generator import RegexGenerator

script_dir = os.path.dirname(os.path.abspath(__file__))
print(script_dir)

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
            self.output_append.emit(f"Critical error in worker thread: {str(e)}")
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

class RegExSearcher(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lobster Log Searcher")
        self.setGeometry(100, 100, 1000, 600)
<<<<<<< Updated upstream
        self.icon = QIcon("_internal/icon/lobster_logo.ico")
=======
        
        # Settings to save current location of the windows on exit
        self.settings = QSettings("App","RegExSearcher")
        geometry = self.settings.value("geometry", bytes())
        self.restoreGeometry(geometry)
        
        self.icon = QIcon("_internal/icon/geis.ico")
>>>>>>> Stashed changes
        self.setWindowIcon(self.icon)
        self.current_theme = os.path.join(script_dir, "_internal/themes/dark_theme.qss") # Sets the global main theme from the file
        self.init_ui()
        self.create_menu_bar()
        self.initialize_theme(self.current_theme)
        self.regex_thread = None
        self.regex_worker = None
        
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
        
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Open Menu
        open_menu = menubar.addMenu("&Open")
        
        open_csv_folder = QAction("Open Output Folder", self)
        open_csv_folder.triggered.connect(lambda: self.open_folder_helper_method(os.path.join(script_dir, "CSVResults")))
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
        job_number_action.triggered.connect(lambda: self.set_pattern(r"Job:\s+((?:\d+|GENERAL))", "Job Number"))
        expressions_menu.addAction(job_number_action)

        profilename_action = QAction("Profilename Pattern", self)
        profilename_action.triggered.connect(lambda: self.set_pattern(r"\[(.*?)]", "Profilename"))
        expressions_menu.addAction(profilename_action)

        filename_action = QAction("Filename Pattern", self)
        filename_action.triggered.connect(lambda: self.set_pattern(r"Start processing data of file '(.*?)'", "Filename"))
        expressions_menu.addAction(filename_action)

        filesize_action = QAction("Filesize Pattern", self)
        filesize_action.triggered.connect(lambda: self.set_pattern(r"length=(\d+),", "Filesize in Bytes"))
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

        # Search button
        self.search_button = QPushButton("Search and Save to CSV")
        self.search_button.clicked.connect(self.start_regex_and_save)
        self.stop_search_button = QPushButton("Abort Task")
        self.stop_search_button.setDisabled(True)
        self.stop_search_button.clicked.connect(self.stop_search_and_save)
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
            self.output_window.setText(f"Generated the following RegEx: '{self.generator.get_regex()}'.\n Press 'Add' to add it to the list")
        else:
            QMessageBox.warning(self, "Input warning", "No string has been entered in the input element.")
    
    def refresh_theme(self):
        try:
            self.initialize_theme(self.current_theme)
        except Exception as ex:
            self.output_window.setText(f"An exception occurred: {str(ex)}")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "", "Log Files (*.log)")
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
        self.search_button.setDisabled(True)
        
        # Start the Thread
        self.regex_thread.start()
        
    def stop_search_and_save(self):
        if hasattr(self, "regex_worker"):
            self.regex_worker.stop()
            self.output_window.setText("Aborting task, please wait...")
            
    def on_finished_search_and_save(self):
        self.stop_search_button.setDisabled(True)
        self.search_button.setDisabled(False)
        self.progress_bar.reset()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegExSearcher()
    window.show()
    app.exec()
