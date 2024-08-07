import os
import re
import csv
import sys
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QListWidget, QLabel, QFileDialog, 
                               QTextEdit, QMenuBar, QMenu, QFrame, QMessageBox)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from _internal.modules.regex_generator import RegexGenerator
from qt_material import apply_stylesheet

class RegExSearcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RegEx Searcher")
        self.setGeometry(100, 100, 1000, 600)
        self.icon = QIcon("_internal/icon/geis.ico")
        self.setWindowIcon(self.icon)
        
        self.current_theme = "_internal/themes/dark_theme.xml"
        apply_stylesheet(self,self.current_theme)

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
        generate_button.clicked.connect(self.generate_regex)
        
        regex_builder_layout.addWidget(self.build_input)
        regex_builder_layout.addWidget(generate_button)

        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a log file...")
        file_button = QPushButton("Browse")
        file_button.setMinimumWidth(100)
        file_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(file_button)

        # RegEx pattern input
        pattern_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter RegEx pattern...")
        add_button = QPushButton("Add")
        add_button.setMinimumWidth(100)
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
        search_button = QPushButton("Search and Save to CSV")
        search_button.clicked.connect(self.search_and_save)

        # Output window
        group_label = QLabel("Program Output:")
        group_label.setStyleSheet("font-size: 20;font-weight: bold")
        self.output_window = QTextEdit()
        self.output_window.setReadOnly(True)

        # Add widgets to layouts
        left_layout.addLayout(file_layout)
        left_layout.addLayout(regex_builder_layout)
        left_layout.addLayout(pattern_layout)
        left_layout.addWidget(self.pattern_list)
        left_layout.addWidget(QLabel("Enter CSV Headers (comma separated):"))
        left_layout.addWidget(self.headers_input)
        left_layout.addWidget(search_button)

        right_layout.addWidget(group_label)
        right_layout.addWidget(self.output_window)

        # Add layouts to main layout
        main_layout.addLayout(left_layout)
        main_layout.addWidget(QFrame(frameShape=QFrame.VLine))
        main_layout.addLayout(right_layout)

        # Set main widget layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create menu bar
        self.create_menu_bar()

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
        
    def generate_regex(self):
        input_element = self.build_input.text()
        if len(input_element) > 0:
            self.generator = RegexGenerator(self.build_input.text())
            self.pattern_input.setText(self.generator.get_regex())
            self.output_window.setText(f"Generated the following RegEx: '{self.generator.get_regex()}'.\n Press 'Add' to add it to the list")
        else:
            QMessageBox.critical(self, "Input error", "No string has been entered in the input element.")

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

    def set_pattern(self, pattern, header):
        self.pattern_input.setText(pattern)
        current_headers = self.headers_input.text()
        if current_headers:
            self.headers_input.setText(f"{current_headers},{header}")
        else:
            self.headers_input.setText(header)

    def search_and_save(self):
        file_path = self.file_input.text()
        headers = self.headers_input.text().split(",")
        patterns = [self.pattern_list.item(i).text() for i in range(self.pattern_list.count())]
        
        print(len(headers),len(patterns))
        

        if not file_path:
            self.output_window.append("Error: Please select a log file.")
            return

        if len(headers) != len(patterns):
            self.output_window.append("Error: Number of headers must match number of RegEx patterns")
            return

        try:
            self.output_window.setText("Started processing...")
            with open(file_path, "r") as file:
                text = file.read()
        except Exception as e:
            self.output_window.append(f"Error: {e}")
            return

        results = self.regex_search(text, patterns)
        csv_data = list(zip(*results.values()))
        
        today_date = datetime.now()
        formatted_today_date = today_date.strftime("%d.%m.%y-%H%M%S")

        try:
            os.makedirs("CSVResults", exist_ok=True)
            with open(f"CSVResults/regex_matches_{formatted_today_date}.csv", mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(csv_data)
            
            self.output_window.append(f"Matches saved to regex_matches_{formatted_today_date}.csv")
        except Exception as e:
            self.output_window.append(f"Error: {e}")

    def regex_search(self, text, patterns):
        return {pattern: re.findall(pattern, text) for pattern in patterns}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegExSearcher()
    window.show()
    app.exec()
