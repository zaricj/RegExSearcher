import csv
import os
import re
import sys
import pandas as pd
import datetime
from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QMessageBox,
)

# Constants
STYLESHEET_THEME = """
QWidget {
    background-color: #232428;
    color: #ffffff;
    border-radius: 4px;
}

QMenuBar {
    background-color: #232428;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #ffc857;
    border-radius: 4px;
    color: #1e1e1e;
}

QMenu {
    background-color: #232428;
    border: 1px solid #313338;
    border-radius: 2px;
}

QMenu::item:selected {
    background-color: #ffc857;
    color: #1e1e1e;
}

QPushButton {
    background-color: #ffc857;
    color: #000000;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    font: bold;
}

QPushButton:hover {
    background-color: #e2b04f;
}

QPushButton:pressed {
    background-color: #a3803c;
}

QPushButton:disabled {
    background-color: #808080;
}

QPushButton#export_to_excel {
    background-color: #21a366;
    color: #000000;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    font: bold;
}

QPushButton#export_to_excel:hover {
    background-color: #228b58;
}

QPushButton#export_to_excel:pressed {
    background-color: #21754b;
}

QPushButton#export_to_excel_summary {
    background-color: #21a366;
    color: #000000;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    font: bold;
}

QPushButton#export_to_excel_summary:hover {
    background-color: #228b58;
}

QPushButton#export_to_excel_summary:pressed {
    background-color: #21754b;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #313338;
    border: 1px solid #4a4a4a;
    padding: 4px 12px;
    border-radius: 4px;
}

QStatusBar {
    background-color: #313338;
    border: 1px solid #4a4a4a;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 16px;
    font: bold;
    color: #20df85;
}

QListWidget {
    background-color: #313338;
}

QListWidget::item {
    height: 26px;
}

QListWidget::item:selected {
    background-color: #ffc857;
    color: #000000;
}

QComboBox::drop-down {
    border: none;
    background-color: #ffc857;
    width: 20px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox:disabled {
    background-color: #808080;    
}

QComboBox::drop-down:disabled {
    border: none;
    background-color: #3d3d3d;
}

QTabWidget::pane {
    border: 1px solid #313338;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #232428;
    border: 1px solid #313338;
    padding: 4px 12px;;
    border-radius: 4px;
    margin: 0 2px;
}

QTabBar::tab:selected {
    background-color: #ffc857;
    color: #000000;
}

QTableView {
    background-color: #313338;
}

QGroupBox {
    border: 1px solid #313338;
    border-radius: 4px;
    margin-top: 10px;
    padding: 10px;
    font: bold;
    color: #ffc857;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QRadioButton:disabled {
    color: #808080; 
}

QScrollBar:vertical {
    border: none;
    background: #232428;
    width: 12px;
    margin: 4px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #313338;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Progress Bar */
QProgressBar {
    background-color: #313338;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    padding: 1px 2px;
}

QProgressBar::chunk {
    background-color: #21a366;
}

/* CheckBox */
QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    background-color: #313338;
    border: 1px solid #4a4a4a;
}

QCheckBox::indicator:checked {
    background-color: #ffc857;
    border: 1px solid #ec971f;
}

QCheckBox::indicator:unchecked {
    background-color: #313338;
    border: 1px solid #4a4a4a;
}
"""

class GenericWorker(QThread):
    output_window = Signal(str)
    status = Signal(str)
    finished = Signal(str)
    progress_value = Signal(int)
    cancel_requested = Signal()
    messagebox_warn = Signal(str, str)
    messagebox_info = Signal(str, str)
    messagebox_crit = Signal(str, str)
    output_window_clear = Signal()

    def __init__(self, task, *args, **kwargs):
        super().__init__()
        self.task = task  # A string to identify the task: "export_excel" or "search_logs"
        self.args = args  # Arguments for the task
        self.kwargs = kwargs # Keyword arguments for the task
        self._is_cancelled = False
        self.cancel_requested.connect(self.cancel)


    def cancel(self):
        self._is_cancelled = True


    def run(self):
        if self.task == "export_excel":
            self.export_csv_to_excel(*self.args, **self.kwargs)
        elif self.task == "write_log_data_to_csv":
            self.extract_and_write_to_csv(*self.args, **self.kwargs)
        # Add more tasks as needed
        else:
            raise ValueError(f"Unknown task: {self.task}")


    def export_csv_to_excel(self, csv_file_path, excel_file_path):
            if not csv_file_path:
                self.messagebox_warn.emit(
                    "No CSV File", "Please select a CSV file to convert."
                )
                return
            else:
                self.output_window.emit("Exporting CSV to Excel... please wait.")
    
            try:
                with open(csv_file_path, encoding="utf-8") as file:
                    sample = file.read(2048)
                    sniffer = csv.Sniffer()
                    get_delimiter = sniffer.sniff(sample).delimiter
                    
                csv_df = pd.read_csv(
                    csv_file_path,
                    delimiter=get_delimiter,
                    encoding="utf-8",
                    engine="pyarrow",
                    index_col=0,
                )
                csv_row_count = csv_df.shape[0]
                
                if csv_row_count < 1048576:
                    # Export to Excel
                    with pd.ExcelWriter(excel_file_path, engine="xlsxwriter") as writer:
                        csv_df.to_excel(writer, sheet_name="Statistics Data", index=False)
    
                    self.messagebox_info.emit(
                        "Successful conversion",
                        f"Successfully converted:\n{csv_file_path}\nto\n{excel_file_path}",
                    )
                else:
                    self.messagebox_warn.emit("Too many rows", f"The CSV file exceeds the maximum row limit 1048576 for Excel. Your file contains {csv_row_count} rows.\nFile conversion not possible.")
                self.output_window_clear.emit()
    
            except Exception as ex:
                message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
                self.messagebox_crit.emit(
                    "Exception exporting CSV", f"Error exporting CSV: {message}"
                )


    def process_file(self, filepath, file_index, total_files):
        if self._is_cancelled:
            return

        total_lines = self.count_lines(filepath)
        if total_lines == 0:
            self.output_window.emit(f"Skipping empty file: {filepath}")
            return

        filename = os.path.basename(filepath)
        self.output_window.emit(
            f"Processing {filename}... (Filesize: {os.path.getsize(filepath)} bytes, {total_lines} lines)"
        )
        self.progress_value.emit(
            int((file_index / total_files) * 100)
        )  # High-level file progress

        with open(filepath, "r", encoding="utf-8", errors="ignore") as log_file:
            for idx, line in enumerate(log_file, start=1):
                if self._is_cancelled:
                    break

                extracted_info = self.extract_info_from_line(line)
                if extracted_info:
                    yield extracted_info

                if (
                    idx % 100 == 0 or idx == total_lines
                ):  # Update progress every 100 lines or at the end
                    percent = int((idx / total_lines) * 100)
                    self.status.emit(
                        f"Processing file {file_index}/{total_files} - Current file progress: {percent}% completed"
                    )

        self.output_window.emit(">>> Finished processing log file.")


    def extract_and_write_to_csv(self, filepath, output_file_csv):
        if os.path.isfile(filepath):
            files = [filepath]
        elif os.path.isdir(filepath):
            files = [
                os.path.join(filepath, f)
                for f in os.listdir(filepath)
                if f.endswith("_message.log")
            ]
        else:
            self.output_window.emit("Invalid filepath.")
            return

        total_matches = 0

        if not self._is_cancelled:
            try:
                with open(
                    output_file_csv, "w", newline="", encoding="utf-8"
                ) as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        [
                            "Time",
                            "Job Number",
                            "Profile Name",
                            "Filename",
                            "Filesize in Bytes",
                        ]
                    )

                    for idx, file in enumerate(files, start=1):
                        if self._is_cancelled:
                            break

                        for row in self.process_file(file, idx, len(files)):
                            writer.writerow(row)
                            total_matches += 1

                self.finished.emit(
                    f"\nData written to: {output_file_csv}\n"
                    f"Total Log Files: {len(files)}\n"
                    f"Total Matches: {total_matches}"
                )
            except Exception as e:
                self.output_window.emit(f"Error writing to CSV: {e}")
        else:
            self.output_window.emit("Operation cancelled by user.")


    # Add helper methods here (e.g., count_lines, extract_info_from_line) if they are used by multiple tasks
    def count_lines(self, filepath):
        count = 0
        with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
            for _ in file:
                count += 1
        return count


    def extract_info_from_line(self, line):
        time_pattern = r"\b(\d{2}:\d{2}:\d{2})\b"
        job_number_pattern = r"Job:\s+((?:\d+|GENERAL))"
        profilename_pattern = r"\[(.*?)]"
        filename_pattern = r"Start processing data of file '(.*?)'"
        filesize_pattern = r"length=(\d+),"

        time_match = re.search(time_pattern, line)
        job_number_match = re.search(job_number_pattern, line)
        profilename_match = re.search(profilename_pattern, line)
        filename_match = re.search(filename_pattern, line)
        filesize_match = re.search(filesize_pattern, line)

        if (
            time_match
            and job_number_match
            and profilename_match
            and filename_match
            and filesize_match
        ):
            return [
                time_match.group(1),
                job_number_match.group(1),
                profilename_match.group(1),
                filename_match.group(1),
                filesize_match.group(1),
            ]
        return None


class StatisticsWindow(QMainWindow):
    
    def __init__(self, csv_path):
        super().__init__()
        self.csv_path = csv_path
        self.setWindowTitle(f"Statistics for {os.path.basename(csv_path)}")
        self.setWindowIcon(
            QIcon(os.path.join(os.getcwd(), "_internal", "icon", "wood.ico"))
        )
        self.resize(800, 600)
        self.setStyleSheet(STYLESHEET_THEME)
        self.statistics_dataframes = {}  # To store dataframes for export

        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        self.create_summary_tab()
        # self.create_profile_size_analysis_tab() # 07.05.2025 commented out
        # self.create_filetype_analysis_tab() # 07.05.2025 commented out

        self.show()


    def closeEvent(self, event):
        self.central_widget.deleteLater()  # Clean up the tab widget
        self.deleteLater()  # Clean up the stats window
        event.accept()  # Accept the close event


    def create_summary_tab(self):
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)

        try:
            usecols = ["Filename", "Filesize in Bytes", "Profile Name"]
            df = pd.read_csv(self.csv_path, usecols=usecols, engine="pyarrow")

            size_stats = df["Filesize in Bytes"].agg(["sum", "mean", "max", "min", "median", "std"])
            total_files = df["Filename"].nunique()
            total_entries = len(df)
            total_size = size_stats["sum"]
            avg_size = size_stats["mean"]
            max_size = size_stats["max"]
            min_size = size_stats["min"]
            median_size = size_stats["median"]
            std_dev_size = size_stats["std"]
            files_by_profile = df["Profile Name"].value_counts()
            top_10_largest = df.nlargest(10, "Filesize in Bytes")[["Filename", "Filesize in Bytes"]]
            top_10_smallest = df.nsmallest(10, "Filesize in Bytes")[["Filename", "Filesize in Bytes"]]

            summary_text.append("<h2>Summary Statistics</h2>")
            summary_text.append(f"<ul><li><b>Einzigartige Dateien insgesamt:</b> {total_files}</li>")
            summary_text.append(f"<li><b>Gesamte Log-Einträge:</b> {total_entries}</li>")
            summary_text.append(f"<li><b>Gesamtgröße:</b> {int(total_size)} bytes ({total_size / 1024 / 1024:.2f} MB)</li>")
            summary_text.append(f"<li><b>Durchschnittliche Dateigröße:</b> {int(avg_size)} bytes ({avg_size / 1024:.2f} KB)</li>")
            summary_text.append(f"<li><b>Größte Datei:</b> {int(max_size)} bytes ({max_size / 1024 / 1024:.2f} MB)</li>")
            summary_text.append(f"<li><b>Kleinste Datei:</b> {int(min_size)} bytes ({min_size / 1024:.2f} KB)</li></ul><br>")
            summary_text.append("<h2>Additional Statistics</h2>")
            summary_text.append(f"<ul><li><b>Mittlere Dateigröße:</b> {median_size:,} bytes ({median_size / 1024:.2f} KB)</li>")
            summary_text.append(f"<li><b>Standardabweichung der Dateigrößen:</b> {std_dev_size:,} bytes ({std_dev_size / 1024:.2f} KB)</li></ul><br>")
            summary_text.append("<h2>Top 10 Largest Files:</h2><br>")
            for _, row in top_10_largest.iterrows():
                summary_text.append(f"<p>{row['Filename']}: {row['Filesize in Bytes']:,} bytes</p>")
            summary_text.append("<br><h2>Top 10 Smallest Files:</h2><br>")
            for _, row in top_10_smallest.iterrows():
                summary_text.append(f"<p>{row['Filename']}: {row['Filesize in Bytes']:,} bytes</p>")
            summary_text.append("<br><h2>Files by Profile Name (First 100 Profiles):</h2><br>")
            for index, (profile, count) in enumerate(files_by_profile.items(), 1):
                if index <= 100:
                    summary_text.append(f"<p>{profile}: {count} files</p>")
                else:
                    break

            summary_layout.addWidget(summary_text)

            export_button = QPushButton("Export to Excel")
            export_button.setObjectName("export_to_excel_summary")
            export_button.setToolTip("Save the statistics as an Excel file")
            export_button.clicked.connect(self.export_excel)
            summary_layout.addWidget(export_button)

            self.central_widget.addTab(summary_tab, "Summary")

        except Exception as e:
            summary_text.append(f"Error calculating summary statistics: {str(e)}")
            summary_layout.addWidget(summary_text)
            self.central_widget.addTab(summary_tab, "Summary")


    def create_profile_size_analysis_tab(self):
        profile_size_tab = QWidget()
        profile_size_layout = QVBoxLayout(profile_size_tab)
        profile_size_text = QTextEdit()
        profile_size_text.setReadOnly(True)

        try:
            df = pd.read_csv(self.csv_path, usecols=["Filename", "Filesize in Bytes", "Profile Name"], engine="pyarrow")

            profile_size_summary = (
                df.groupby("Profile Name")
                .agg(
                    {
                        "Filesize in Bytes": ["mean", "std", "min", "max", "count"],
                        "Filename": lambda x: list(dict.fromkeys(filter(None, x)))[:5],
                    }
                )
                .reset_index()
            )
            profile_size_summary.columns = [
                "Profile Name",
                "Avg File Size (Bytes)",
                "Std File Size (Bytes)",
                "Min File Size (Bytes)",
                "Max File Size (Bytes)",
                "Count",
                "Filenames",
            ]
            profile_size_summary["Avg File Size (Bytes)"] = profile_size_summary["Avg File Size (Bytes)"].round(2)
            profile_size_summary["Std File Size (Bytes)"] = profile_size_summary["Std File Size (Bytes)"].round(2)
            profile_size_summary["Filenames"] = profile_size_summary["Filenames"].apply(lambda x: ", ".join(x) if x else "None")

            profile_size_text.append("<h2>Profile File Size Analysis</h2><br>")
            profile_size_text.append(profile_size_summary.to_html(index=False))
            profile_size_layout.addWidget(profile_size_text)
            self.central_widget.addTab(profile_size_tab, "Profile File Size")

            # Store for export
            profile_size_export_df = profile_size_summary.copy()
            self.statistics_dataframes["Per Profile Statistics"] = profile_size_export_df

        except Exception as e:
            profile_size_text.append(f"Error calculating profile size analysis: {str(e)}")
            profile_size_layout.addWidget(profile_size_text)
            self.central_widget.addTab(profile_size_tab, "Profile File Size")


    def create_filetype_analysis_tab(self):
        filetype_tab = QWidget()
        filetype_layout = QVBoxLayout(filetype_tab)
        filetype_text = QTextEdit()
        filetype_text.setReadOnly(True)

        try:
            df = pd.read_csv(self.csv_path, usecols=["Filename"], engine="pyarrow")
            df["Filetype"] = df["Filename"].str.extract(r'\.([^.]+)$').fillna("unknown")
            filetypes_df = df["Filetype"].value_counts().head(20).reset_index()
            filetypes_df.columns = ["Filetype", "File Count"]

            filetype_text.append("<h2>Top 20 File Types</h2><br>")
            filetype_text.append(filetypes_df.to_html(index=False))
            filetype_layout.addWidget(filetype_text)
            self.central_widget.addTab(filetype_tab, "File Types")

            # Store for export
            self.statistics_dataframes["Top Filetypes"] = filetypes_df

        except Exception as e:
            filetype_text.append(f"Error analyzing file types: {str(e)}")
            filetype_layout.addWidget(filetype_text)
            self.central_widget.addTab(filetype_tab, "File Types")


    def export_excel(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Excel File",
                f"{os.path.basename(self.csv_path).split('.')[0]}_statistics_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx",
                "Excel Files (*.xlsx)",
            )
            if not file_path:
                return  # User canceled

            with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
                for sheet_name, df_export in self.statistics_dataframes.items():
                    df_export.to_excel(writer, sheet_name=sheet_name, index=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported to:\n{file_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))


class LogSearcherGUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lobster Message Log Searcher v1.0")
        self.setWindowIcon(
            QIcon(os.path.join(os.getcwd(), "_internal", "icon", "wood.ico"))
        )
        # Initialize settings for window geometry
        self.settings = QSettings(
            "Application", "Name"
        )  # Settings to save current location of the windows on exit
        geometry = self.settings.value("app_geometry", bytes())

        # Load recent folders
        self.recent_folders = self.settings.value("recent_folders", [], type=list)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.restoreGeometry(geometry)

        self.setup_ui()
        self.apply_stylesheet()


    def setup_ui(self):
        self.setup_menubar()

        # Log Processing Input Group
        input_group = QGroupBox("Log Processing Input")
        input_layout = QVBoxLayout(input_group)

        input_layout.addWidget(QLabel("Log Files Location"))
        self.log_filepath_layout = QHBoxLayout()
        self.log_filepath_input = QLineEdit()
        self.log_filepath_input.setPlaceholderText(
            "Select a folder that contains lobster message logs..."
        )
        self.log_filepath_button = QPushButton("Browse")
        self.log_filepath_button.clicked.connect(self.browse_log_folder)
        self.log_filepath_layout.addWidget(self.log_filepath_input)
        self.log_filepath_layout.addWidget(self.log_filepath_button)
        input_layout.addLayout(self.log_filepath_layout)

        input_layout.addWidget(QLabel("Output CSV Location"))
        self.csv_result_layout = QHBoxLayout()
        self.csv_result_input = QLineEdit()
        self.csv_result_input.setPlaceholderText(
            "Select a folder where to save the CSV result file..."
        )
        self.csv_result_button = QPushButton("Browse")
        self.csv_result_button.clicked.connect(self.browse_csv_save)
        self.csv_result_layout.addWidget(self.csv_result_input)
        self.csv_result_layout.addWidget(self.csv_result_button)
        input_layout.addLayout(self.csv_result_layout)

        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.cancel_button)
        input_layout.addLayout(controls_layout)

        self.layout.addWidget(input_group)

        # Log Processing Output Group
        output_group = QGroupBox("Log Processing Output")
        output_layout = QVBoxLayout(output_group)

        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        output_layout.addWidget(self.progress_bar)

        self.program_output_window = QTextEdit()
        self.program_output_window.setReadOnly(True)

        # Add widgets to output layout
        output_layout.addWidget(self.program_output_window)
        output_layout.addWidget(self.status_bar)

        self.layout.addWidget(output_group)

        # File Size Summary Group
        summary_group = QGroupBox("File Size Summary")
        summary_layout = QVBoxLayout(summary_group)

        summary_layout.addWidget(
            QLabel("Select CSV File for Summary or Excel Conversion")
        )
        self.csv_sum_layout = QHBoxLayout()
        self.csv_sum_filepath_input = QLineEdit()
        self.csv_sum_filepath_input.setPlaceholderText(
            "Select a CSV file to summarize or to convert to Excel..."
        )
        self.csv_sum_filepath_button = QPushButton("Browse")
        self.csv_sum_filepath_button.clicked.connect(self.browse_csv_sum)
        self.summarize_button = QPushButton("Calculate Summary")
        self.export_to_excel = QPushButton("Export to Excel")
        self.export_to_excel.setObjectName("export_to_excel")
        self.export_to_excel.clicked.connect(self.export_to_excel_triggered)
        self.summarize_button.clicked.connect(self.summarize_filesize)
        self.show_more_statistics = QPushButton("Show More Statistics")
        self.show_more_statistics.setHidden(True)  # Initially hidden
        self.show_more_statistics.clicked.connect(self.show_statistics_window)
        self.csv_sum_layout.addWidget(self.csv_sum_filepath_input)
        self.csv_sum_layout.addWidget(self.csv_sum_filepath_button)
        self.csv_sum_layout.addWidget(self.summarize_button)
        self.csv_sum_layout.addWidget(self.export_to_excel)

        summary_layout.addLayout(self.csv_sum_layout)

        self.summary_output_text = QTextEdit()
        self.summary_output_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_output_text)
        summary_layout.addWidget(self.show_more_statistics)

        self.layout.addWidget(summary_group)
    
    
    def summarize_filesize(self):
            # Clear output
            self.summary_output_text.setText("Calculating Total Filesize in Bytes... please wait.")
            self.progress_bar.setValue(0)
            csv_result_path = self.csv_sum_filepath_input.text()
            try:
                df = pd.read_csv(csv_result_path)
                total_filesize = df["Filesize in Bytes"].sum()

                kb = total_filesize / 1024
                mb = kb / 1024
                gb = mb / 1024

                summary = (
                    f"Total Filesize of all processed files:\n"
                    f"In Bytes = {total_filesize:,}\n"
                    f"In KB = {kb:,.2f}\n"
                    f"In MB = {mb:,.2f}\n"
                    f"In GB = {gb:,.2f}"
                )

                self.summary_output_text.clear()
                self.summary_output_text.append(summary)

                # Preview first few rows
                # preview = df.head().to_string(index=False)
                # self.summary_output_text.append("\nCSV Preview (First 5 Rows):\n" + preview)

                self.show_more_statistics.setHidden(
                    False
                )  # Show the button after summarization

            except FileNotFoundError:
                self.summary_output_text.append("No such file or directory.")
            except Exception as e:
                self.summary_output_text.append(f"Error processing CSV: {str(e)}")
                
                
    def show_statistics_window(self):
        csv_path = self.csv_sum_filepath_input.text()
        if not csv_path:
            self.program_output_window.setText(
                "No CSV file to open and show additional statistics."
            )
            return
        self.statistics_window = StatisticsWindow(csv_path)
        
        
    def apply_stylesheet(self):
        self.setStyleSheet(STYLESHEET_THEME)


    def setup_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        self.recent_menu = QMenu("Recent Folders", self)
        self.recent_menu.clear()

        for folder in self.recent_folders:
            action = QAction(folder, self)
            action.triggered.connect(lambda checked, p=folder: self.open_logs_folder(p))
            self.recent_menu.addAction(action)

        file_menu.addMenu(self.recent_menu)

        file_menu.addSeparator()

        clear_recent_action = QAction("Clear Recent Folders", self)
        clear_recent_action.triggered.connect(self.clear_recent_folders)
        file_menu.addAction(clear_recent_action)

        file_menu.addSeparator()

        clear_output = QAction("Clear Output", self)
        clear_output.triggered.connect(self.clear_output)
        file_menu.addAction(clear_output)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        presets_menu = menubar.addMenu("&Presets")
        open_test_logs = QAction("//nesist02/hub/logs/DataWizard", self)
        open_test_logs.triggered.connect(
            lambda: self.open_logs_folder("//nesist02/hub/logs/DataWizard")
        )
        presets_menu.addAction(open_test_logs)
        open_prod_logs = QAction("//nesis002/hub/logs/DataWizard", self)
        open_prod_logs.triggered.connect(
            lambda: self.open_logs_folder("//nesis002/hub/logs/DataWizard")
        )
        presets_menu.addAction(open_prod_logs)
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)


    def browse_log_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Log Folder")
        if folder:
            self.log_filepath_input.setText(folder)
            self.add_recent_folder(folder)
            self.print_total_log_files(folder)


    def browse_csv_save(self):
        placeholder_text = (
            os.path.basename(os.path.normpath(self.log_filepath_input.text()))
            if len(self.log_filepath_input.text()) != 0
            else "csv_result"
        )
        file, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", placeholder_text, "CSV Files (*.csv)"
        )
        if file:
            self.csv_result_input.setText(file)


    def browse_csv_sum(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if file:
            self.csv_sum_filepath_input.setText(file)

    # START ======= Main Methods of Program ======== START #

    def export_to_excel_triggered(self) -> None:
        csv_file_path = self.csv_sum_filepath_input.text()
        if not csv_file_path:
            self.program_output_window.append("Please select a CSV file to export.")
            return

        default_name = (
            f"{os.path.basename(csv_file_path).split('.')[0]}_excel_export.xlsx"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", default_name, "Excel Files (*.xlsx)"
        )

        if file_path:
            self.start_export_to_excel(csv_file_path, file_path)
        else:
            self.program_output_window.append("Excel export cancelled by user.")

    # Worker Thread for exporting CSV files to Excel - To combat GUI freezes
    def start_export_to_excel(self, csv_file_path: str, excel_file_path: str) -> None:
        if csv_file_path:
            self.worker = GenericWorker("export_excel",csv_file_path, excel_file_path)
            self.worker.output_window.connect(self.write_to_output_window)
            self.worker.messagebox_info.connect(self.messagebox_popup_info)
            self.worker.messagebox_warn.connect(self.messagebox_popup_warn)
            self.worker.messagebox_crit.connect(self.messagebox_popup_crit)
            self.worker.output_window_clear.connect(self.clear_output_window)
            self.worker.start()
        else:
            self.program_output_window.append("Please select a CSV file to export.")
            

    #  Main method to search log files and write data to csv file
    def start_processing(self):
        log_filepath = self.log_filepath_input.text().strip()
        output_csv = self.csv_result_input.text()

        if not log_filepath:
            self.program_output_window.append("Please select a log files folder.")
        elif not output_csv:
            self.program_output_window.append(
                "Please specify an output CSV file location."
            )
        else:
            # Check if log files have been found in the selected folder
            files = [f for f in os.listdir(log_filepath) if f.endswith(".log")]
            if files:
                self.program_output_window.append(
                    "Starting to process log files... please wait."
                )
                self.start_button.setEnabled(False)
                self.cancel_button.setEnabled(True)
                self.progress_bar.setValue(0)
                self.worker = GenericWorker("write_log_data_to_csv",log_filepath, output_csv)
                self.worker.output_window.connect(self.update_progress)
                self.worker.status.connect(self.update_status)
                self.worker.finished.connect(self.processing_finished)
                self.worker.progress_value.connect(self.update_progress_bar)
                self.worker.start()
            else:
                self.program_output_window.append(
                    "No log files found in the selected folder."
                )

    def open_logs_folder(self, path):
        self.log_filepath_input.setText(path)
        self.add_recent_folder(path)
        self.print_total_log_files(path)

    def add_recent_folder(self, folder):
        if folder not in self.recent_folders:
            self.recent_folders.insert(0, folder)
            if len(self.recent_folders) > 5:
                self.recent_folders.pop()

            self.recent_menu.clear()
            for f in self.recent_folders:
                action = QAction(f, self)
                action.triggered.connect(lambda checked, p=f: self.open_logs_folder(p))
                self.recent_menu.addAction(action)

    def clear_output(self):
        self.program_output_window.clear()
        self.summary_output_text.clear()
        self.progress_bar.setValue(0)

    def show_about(self):
        about_text = """
Lobster Message Log Searcher
Version 1.0
Searches for message .log files only! (*_message.log)

Output CSV Headers:
| Time | Job Number | Profile Name | Filename | Filesize in Bytes

Features:
- Progress tracking
- Filesize summarization
- Recent folders history"""
        self.program_output_window.append(about_text)

    # Clear the recent folders from QSettings and the "Recent Menu" Menubar
    def clear_recent_folders(self):
        # Remove the 'recent_folders' key from QSettings
        self.settings.remove("recent_folders")

        # Clear the in-memory list of recent folders
        self.recent_folders = []

        # Clear the Recent Folders menu in the GUI
        self.recent_menu.clear()

    # Program close event trigger
    def closeEvent(self, event: QCloseEvent):
        # Save geometry on close
        geometry = self.saveGeometry()
        self.settings.setValue("app_geometry", geometry)
        # Save recent folders
        self.settings.setValue("recent_folders", self.recent_folders)
        super(LogSearcherGUI, self).closeEvent(event)

    # Prints the total log files found in the statusbar
    def print_total_log_files(self, filepath):
        try:
            if os.path.isfile(filepath):
                files = [filepath]
            elif os.path.isdir(filepath):
                files = [f for f in os.listdir(filepath) if f.endswith("_message.log")]
                self.status_bar.showMessage(f"Total log files found: {len(files)}")
            else:
                self.status_bar.clearMessage()
        except (TypeError, FileNotFoundError):
            self.status_bar.clearMessage()

    # ====== Slots for the Signals ====== #
    
    def write_to_output_window(self, message):
        self.program_output_window.setText(message)
        
    def clear_output_window(self):
        self.program_output_window.clear()

    def messagebox_popup_info(self, title, message):
        QMessageBox.information(self, title, message)

    def messagebox_popup_warn(self, title, message):
        QMessageBox.warning(self, title, message)

    def messagebox_popup_crit(self, title, message):
        QMessageBox.critical(self, title, message)
        
    def cancel_processing(self):
        if hasattr(self, "worker"):
            self.worker.cancel_requested.emit()
            self.cancel_button.setEnabled(False)
            self.start_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.program_output_window.setText("Canceling operation please wait...")
            self.status_bar.showMessage("")

    def update_progress(self, message):
        self.program_output_window.append(message)
        self.program_output_window.ensureCursorVisible()

    def update_status(self, message):
        self.status_bar.showMessage(message)

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def processing_finished(self, message):
        self.program_output_window.append(message)
        self.status_bar.showMessage("Processing complete!", 5000)
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)

    # ====== END Slots for the Signals END ====== #


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogSearcherGUI()
    window.show()
    sys.exit(app.exec())
