from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QProgressBar, QApplication
import sys
import time

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    progress = Signal(int)    # Signal for progress updates
    finished = Signal()       # Signal when task is complete
    error = Signal(str)       # Signal for error reporting

class Worker(QObject):
    """
    Worker class that will run in a separate thread.
    This is a blueprint for implementing any long-running task.
    """
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_running = True
    
    def stop(self):
        """Method to stop the running task"""
        self._is_running = False
    
    def run(self):
        """
        The actual task that will run in the thread.
        This is a sample implementation - modify for your specific task.
        """
        try:
            # Simulate a long-running task
            for i in range(100):
                # Check if we should stop
                if not self._is_running:
                    break
                
                # Do some work here
                time.sleep(0.1)  # Simulate work
                
                # Emit progress
                self.signals.progress.emit(i + 1)
            
            # Emit finished signal
            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Threading Example")
        self.setup_ui()
        self.thread = None
        self.worker = None

    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create start button
        self.start_button = QPushButton("Start Task")
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        # Create abort button
        self.abort_button = QPushButton("Abort")
        self.abort_button.clicked.connect(self.abort_task)
        self.abort_button.setEnabled(False)
        layout.addWidget(self.abort_button)

        # Create progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def start_task(self):
        # Create a new thread and worker
        self.thread = QThread()
        self.worker = Worker()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.task_finished)
        self.worker.signals.error.connect(self.handle_error)
        
        # Update UI state
        self.start_button.setEnabled(False)
        self.abort_button.setEnabled(True)
        self.progress_bar.setValue(0)
        
        # Start the thread
        self.thread.start()

    def abort_task(self):
        if self.worker:
            self.worker.stop()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def task_finished(self):
        # Clean up thread and worker
        self.thread.quit()
        self.thread.wait()
        self.thread = None
        self.worker = None
        
        # Reset UI state
        self.start_button.setEnabled(True)
        self.abort_button.setEnabled(False)
        self.progress_bar.setValue(100)

    def handle_error(self, error_message):
        print(f"Error: {error_message}")
        self.task_finished()  # Clean up

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(300, 150)
    window.show()
    sys.exit(app.exec())
