#!/usr/bin/env python3

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from fb2_gui_ui import Ui_MainWindow
from fb2_db_utils import initialize_database, process_archive, get_processed_archives

class WorkerThread(QThread):
    """Worker thread for processing archives without blocking UI"""
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(int)
    
    def __init__(self, db_path, archives_dir, force_reprocess=False):
        super().__init__()
        self.db_path = db_path
        self.archives_dir = archives_dir
        self.force_reprocess = force_reprocess
        self.running = True
    
    def run(self):
        import tempfile
        from pathlib import Path
        import sqlite3
        
        try:
            conn = initialize_database(self.db_path)
            
            # Get already processed archives if not forcing reprocess
            processed_archives = set()
            if not self.force_reprocess:
                processed_archives = get_processed_archives(conn)
            
            # Find ZIP files in the directory
            archives = [f for f in Path(self.archives_dir).glob('*.zip')]
            self.update_signal.emit(f"Found {len(archives)} archives in directory")
            
            # Process only new archives if not forcing reprocess
            if not self.force_reprocess:
                archives = [a for a in archives if a.name not in processed_archives]
                self.update_signal.emit(f"Processing {len(archives)} new archives")
            
            total_archives = len(archives)
            total_inserted = 0
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, archive in enumerate(archives):
                    if not self.running:
                        break
                    
                    self.update_signal.emit(f"Processing archive: {archive.name}")
                    inserted = process_archive(conn, archive, temp_dir)
                    total_inserted += inserted
                    
                    # Update progress
                    progress = int((i+1) / total_archives * 100)
                    self.progress_signal.emit(progress)
            
            self.update_signal.emit(f"Added {total_inserted} new FB2 files to the database")
            self.finished_signal.emit(total_inserted)
            conn.close()
            
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(-1)
    
    def stop(self):
        self.running = False

class FB2DatabaseManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Connect signals
        self.ui.actionOpen_Database.triggered.connect(self.open_database)
        self.ui.actionCreate_New_Database.triggered.connect(self.create_database)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.buttonSelectArchivesDir.clicked.connect(self.select_archives_dir)
        self.ui.buttonProcess.clicked.connect(self.process_archives)
        self.ui.buttonSearch.clicked.connect(self.search_database)
        # Connect double-click on table to show book details
        self.ui.tableResults.cellDoubleClicked.connect(self.show_book_details)
        
        # Initialize variables
        self.db_path = None
        self.archives_dir = None
        self.worker_thread = None
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def open_database(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open Database", "", "SQLite Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_path = file_path
            self.statusBar().showMessage(f"Database: {os.path.basename(self.db_path)}")
            self.ui.labelDatabase.setText(f"Database: {os.path.basename(self.db_path)}")
            self.update_book_count()
    
    def create_database(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Create Database", "", "SQLite Database Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_path = file_path
            try:
                initialize_database(self.db_path)
                self.statusBar().showMessage(f"Created new database: {os.path.basename(self.db_path)}")
                self.ui.labelDatabase.setText(f"Database: {os.path.basename(self.db_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create database: {str(e)}")
    
    def select_archives_dir(self):
        dir_dialog = QFileDialog()
        dir_path = dir_dialog.getExistingDirectory(self, "Select Archives Directory")
        
        if dir_path:
            self.archives_dir = dir_path
            self.ui.labelArchivesDir.setText(f"Archives Directory: {self.archives_dir}")
    
    def process_archives(self):
        if not self.db_path:
            QMessageBox.warning(self, "Warning", "Please open or create a database first.")
            return
        
        if not self.archives_dir:
            QMessageBox.warning(self, "Warning", "Please select a directory containing FB2 archives.")
            return
        
        force_reprocess = self.ui.checkBoxForceReprocess.isChecked()
        
        # Disable UI elements during processing
        self.ui.buttonProcess.setEnabled(False)
        self.ui.progressBar.setValue(0)
        self.ui.textLog.clear()
        
        # Start worker thread
        self.worker_thread = WorkerThread(self.db_path, self.archives_dir, force_reprocess)
        self.worker_thread.update_signal.connect(self.update_log)
        self.worker_thread.progress_signal.connect(self.ui.progressBar.setValue)
        self.worker_thread.finished_signal.connect(self.processing_finished)
        self.worker_thread.start()
    
    def update_log(self, message):
        self.ui.textLog.append(message)
    
    def processing_finished(self, total_inserted):
        self.ui.buttonProcess.setEnabled(True)
        if total_inserted >= 0:
            self.statusBar().showMessage(f"Processing completed. Added {total_inserted} books.")
            self.update_book_count()
        else:
            self.statusBar().showMessage("Processing failed.")
    
    def update_book_count(self):
        if not self.db_path:
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fb2_files")
            count = cursor.fetchone()[0]
            self.ui.labelBookCount.setText(f"Total books: {count}")
            conn.close()
        except Exception as e:
            self.ui.labelBookCount.setText("Total books: Unknown")
    
    def search_database(self):
        if not self.db_path:
            QMessageBox.warning(self, "Warning", "Please open a database first.")
            return
        
        search_text = self.ui.lineEditSearch.text().strip()
        if not search_text:
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear the table
            self.ui.tableResults.setRowCount(0)
            
            # Search in FTS table
            cursor.execute("""
                SELECT fb2_files.id, fb2_files.title, fb2_files.author, fb2_files.year, 
                       fb2_files.publisher, fb2_files.outer_zip, fb2_files.inner_zip, fb2_files.size
                FROM fb2_search 
                JOIN fb2_files ON fb2_search.rowid = fb2_files.id
                WHERE fb2_search MATCH ?
                LIMIT 1000
            """, (search_text,))
            
            # Add results to table
            for row_data in cursor.fetchall():
                row_position = self.ui.tableResults.rowCount()
                self.ui.tableResults.insertRow(row_position)
                
                for column, value in enumerate(row_data):
                    from PyQt6.QtWidgets import QTableWidgetItem
                    self.ui.tableResults.setItem(row_position, column, QTableWidgetItem(str(value)))
            
            conn.close()
            self.statusBar().showMessage(f"Found {self.ui.tableResults.rowCount()} results")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")
    
    def show_book_details(self, row, column):
        if not self.db_path:
            return
        
        # Get book data from the selected row
        book_data = {}
        book_data['id'] = self.ui.tableResults.item(row, 0).text()
        book_data['title'] = self.ui.tableResults.item(row, 1).text()
        book_data['author'] = self.ui.tableResults.item(row, 2).text()
        book_data['year'] = self.ui.tableResults.item(row, 3).text()
        book_data['publisher'] = self.ui.tableResults.item(row, 4).text()
        book_data['outer_zip'] = self.ui.tableResults.item(row, 5).text()
        book_data['inner_zip'] = self.ui.tableResults.item(row, 6).text()
        book_data['size'] = self.ui.tableResults.item(row, 7).text()
        book_data['db_path'] = self.db_path
        
        # Pass the archives directory to the dialog
        archives_dir = self.archives_dir if hasattr(self, 'archives_dir') and self.archives_dir else ""
        
        from fb2_book_dialog import BookDetailsDialog
        dialog = BookDetailsDialog(self, book_data, archives_dir)
        dialog.exec()
    
    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit", 
                "Processing is still running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.stop()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()

def main():
    app = QApplication(sys.argv)
    window = FB2DatabaseManagerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()