from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
import zipfile
import tempfile
import xml.etree.ElementTree as ET

class ExtractThread(QThread):
    """Thread for extracting FB2 file from archive"""
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, archive_path, file_path, temp_dir):
        super().__init__()
        self.archive_path = archive_path
        self.file_path = file_path
        self.temp_dir = temp_dir
    
    def run(self):
        try:
            # Extract FB2 file from archive
            with zipfile.ZipFile(self.archive_path, 'r') as zip_file:
                # Get file info
                file_info = zip_file.getinfo(self.file_path)
                total_size = file_info.file_size
                
                # Set up extraction with progress reporting
                extracted_path = os.path.join(self.temp_dir, "book.fb2")
                
                with open(extracted_path, 'wb') as out_file:
                    with zip_file.open(self.file_path) as zip_content:
                        chunk_size = 8192
                        bytes_read = 0
                        
                        while True:
                            chunk = zip_content.read(chunk_size)
                            if not chunk:
                                break
                            
                            out_file.write(chunk)
                            bytes_read += len(chunk)
                            
                            # Update progress
                            if total_size > 0:
                                progress = int(bytes_read / total_size * 100)
                                self.progress_signal.emit(progress)
                
                self.finished_signal.emit(extracted_path)
        
        except Exception as e:
            self.error_signal.emit(str(e))

class BookDetailsDialog(QDialog):
    def __init__(self, parent=None, book_data=None, archives_dir=None):
        super().__init__(parent)
        self.book_data = book_data
        self.archives_dir = archives_dir
        self.temp_dir = None
        self.fb2_path = None
        self.extract_thread = None
        
        self.setWindowTitle("Book Details")
        self.resize(600, 500)
        
        self.setup_ui()
        self.populate_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Book info section
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title_label)
        
        self.author_label = QLabel()
        layout.addWidget(self.author_label)
        
        self.year_publisher_label = QLabel()
        layout.addWidget(self.year_publisher_label)
        
        self.archive_label = QLabel()
        layout.addWidget(self.archive_label)
        
        layout.addSpacing(10)
        
        # Content preview
        self.content_label = QLabel("Content:")
        layout.addWidget(self.content_label)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        layout.addWidget(self.content_text)
        
        # Extract progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.extract_button = QPushButton("Extract Book")
        self.extract_button.clicked.connect(self.extract_book)
        button_layout.addWidget(self.extract_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def populate_data(self):
        if not self.book_data:
            return
        
        self.title_label.setText(self.book_data.get('title', 'Unknown title'))
        self.author_label.setText(f"Author: {self.book_data.get('author', 'Unknown')}")
        
        year = self.book_data.get('year', 'Unknown')
        publisher = self.book_data.get('publisher', 'Unknown')
        self.year_publisher_label.setText(f"Year: {year}, Publisher: {publisher}")
        
        outer_zip = self.book_data.get('outer_zip', '')
        inner_zip = self.book_data.get('inner_zip', '')
        self.archive_label.setText(f"Location: {outer_zip} > {inner_zip}")
        
        # Create temp directory and start extraction
        self.temp_dir = tempfile.mkdtemp()
        self.start_extraction()
    
    def start_extraction(self):
        if not self.book_data:
            return
        
        outer_zip = self.book_data.get('outer_zip', '')
        inner_zip = self.book_data.get('inner_zip', '')
        
        # Check if archive exists
        archives_dir = self.archives_dir or os.path.dirname(self.book_data.get('db_path', ''))
        archive_path = os.path.join(archives_dir, outer_zip)
        
        if not os.path.exists(archive_path):
            self.content_text.setText(f"Error: Archive file not found: {archive_path}")
            return
        
        # Set up progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Start extraction thread
        self.extract_thread = ExtractThread(archive_path, inner_zip, self.temp_dir)
        self.extract_thread.progress_signal.connect(self.progress_bar.setValue)
        self.extract_thread.finished_signal.connect(self.extraction_finished)
        self.extract_thread.error_signal.connect(self.extraction_error)
        self.extract_thread.start()
    
    def extraction_finished(self, file_path):
        self.fb2_path = file_path
        self.progress_bar.setVisible(False)
        
        try:
            # Parse FB2 file and show preview
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Try to extract book description or start of body
            FB2_NS = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Try to get annotation
            annotation = root.find(".//fb:annotation", FB2_NS)
            if annotation is not None:
                text = "".join(annotation.itertext())
                self.content_text.setText(f"Annotation:\n\n{text}")
                return
            
            # If no annotation, try to get beginning of body
            body = root.find(".//fb:body", FB2_NS)
            if body is not None:
                # Get first few paragraphs
                paragraphs = body.findall(".//fb:p", FB2_NS)[:5]
                text = "\n\n".join("".join(p.itertext()) for p in paragraphs if p.text)
                self.content_text.setText(f"Preview:\n\n{text}")
                return
            
            self.content_text.setText("No preview available.")
            
        except Exception as e:
            self.content_text.setText(f"Error parsing FB2 file: {str(e)}")
    
    def extraction_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.content_text.setText(f"Error extracting book: {error_message}")
    
    def extract_book(self):
        if not self.fb2_path:
            QMessageBox.warning(self, "Warning", "Book has not been extracted yet.")
            return
        
        # Create format selection dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        
        format_dialog = QDialog(self)
        format_dialog.setWindowTitle("Select Export Formats")
        format_dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(format_dialog)
        
        # Format checkboxes
        fb2_checkbox = QCheckBox("FB2 (original format)")
        fb2_checkbox.setChecked(True)
               
        epub_checkbox = QCheckBox("EPUB")
        pdf_checkbox = QCheckBox("PDF")
        
        layout.addWidget(QLabel("Choose export formats:"))
        layout.addWidget(fb2_checkbox)
        layout.addWidget(epub_checkbox)
        layout.addWidget(pdf_checkbox)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(format_dialog.accept)
        button_box.rejected.connect(format_dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if format_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get selected formats
        formats = []
        if fb2_checkbox.isChecked():
            formats.append("fb2")
        if epub_checkbox.isChecked():
            formats.append("epub")
        if pdf_checkbox.isChecked():
            formats.append("pdf")
        
        if not formats:
            return
        
        # Let user choose where to save the file(s)
        from PyQt6.QtWidgets import QFileDialog
        
        title = self.book_data.get('title', 'book').replace('/', '_').replace('\\', '_')
        author = self.book_data.get('author', 'unknown').replace('/', '_').replace('\\', '_')
        base_name = f"{author} - {title}"
        
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not directory:
            return
        
        # Process each format
        import shutil
        
        for fmt in formats:
            try:
                if fmt == "fb2":
                    # Just copy the original FB2 file
                    output_path = os.path.join(directory, f"{base_name}.fb2")
                    shutil.copy2(self.fb2_path, output_path)
                    QMessageBox.information(self, "Success", f"Book saved as FB2: {output_path}")
                
                elif fmt == "epub":
                    # Convert FB2 to EPUB
                    output_path = os.path.join(directory, f"{base_name}.epub")
                    self.convert_to_epub(self.fb2_path, output_path)
                    QMessageBox.information(self, "Success", f"Book converted to EPUB: {output_path}")
                
                elif fmt == "pdf":
                    # Convert FB2 to PDF
                    output_path = os.path.join(directory, f"{base_name}.pdf")
                    self.convert_to_pdf(self.fb2_path, output_path)
                    QMessageBox.information(self, "Success", f"Book converted to PDF: {output_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save book as {fmt.upper()}: {str(e)}")
    
    def closeEvent(self, event):
        # Clean up temp directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
        
        # Stop extraction thread if running
        if self.extract_thread and self.extract_thread.isRunning():
            self.extract_thread.terminate()
            self.extract_thread.wait()
        
        event.accept()
    
    def convert_to_epub(self, fb2_path, output_path):
        """Convert FB2 to EPUB format"""
        try:
            # First try using fb2converter if available
            import subprocess
            result = subprocess.run(['fb2converter', fb2_path, output_path], 
                                   capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Basic conversion using XML parsing
        self.content_text.setText("Converting to EPUB format...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            # Parse FB2
            tree = ET.parse(fb2_path)
            root = tree.getroot()
            FB2_NS = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Simple HTML-based EPUB creation
            import zipfile
            import tempfile
            import os
            
            # Create temp directory for EPUB files
            epub_temp = tempfile.mkdtemp()
            
            # Create mimetype file
            with open(os.path.join(epub_temp, "mimetype"), "w") as f:
                f.write("application/epub+zip")
            
            # Create META-INF directory
            os.makedirs(os.path.join(epub_temp, "META-INF"))
            
            # Create container.xml
            with open(os.path.join(epub_temp, "META-INF", "container.xml"), "w") as f:
                f.write('''<?xml version="1.0" encoding="UTF-8"?>
                <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                   <rootfiles>
                      <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
                   </rootfiles>
                </container>''')
            
            # Create content files
            title = self.book_data.get('title', 'Unknown')
            author = self.book_data.get('author', 'Unknown')
            
            # Create title page
            with open(os.path.join(epub_temp, "title.xhtml"), "w", encoding="utf-8") as f:
                f.write(f'''<?xml version="1.0" encoding="utf-8"?>
                <!DOCTYPE html>
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                    <title>{title}</title>
                </head>
                <body>
                    <h1>{title}</h1>
                    <h2>by {author}</h2>
                </body>
                </html>''')
            
            # Extract book content
            body = root.find('.//fb:body', FB2_NS)
            content = ""
            
            if body is not None:
                paragraphs = body.findall('.//fb:p', FB2_NS)
                for p in paragraphs:
                    if p is not None:
                        text = "".join(p.itertext())
                        if text:
                            content += f"<p>{text}</p>\n"
            
            # Create content page
            with open(os.path.join(epub_temp, "content.xhtml"), "w", encoding="utf-8") as f:
                f.write(f'''<?xml version="1.0" encoding="utf-8"?>
                <!DOCTYPE html>
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                    <title>{title}</title>
                </head>
                <body>
                    {content}
                </body>
                </html>''')
            
            # Create content.opf
            with open(os.path.join(epub_temp, "content.opf"), "w", encoding="utf-8") as f:
                f.write(f'''<?xml version="1.0" encoding="utf-8"?>
                <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
                    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
                        <dc:title>{title}</dc:title>
                        <dc:creator>{author}</dc:creator>
                        <dc:language>en</dc:language>
                        <dc:identifier id="BookID">urn:uuid:{os.urandom(16).hex()}</dc:identifier>
                    </metadata>
                    <manifest>
                        <item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>
                        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
                        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
                    </manifest>
                    <spine toc="ncx">
                        <itemref idref="title"/>
                        <itemref idref="content"/>
                    </spine>
                </package>''')
            
            # Create toc.ncx
            with open(os.path.join(epub_temp, "toc.ncx"), "w", encoding="utf-8") as f:
                f.write(f'''<?xml version="1.0" encoding="utf-8"?>
                <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
                    <head>
                        <meta name="dtb:uid" content="urn:uuid:{os.urandom(16).hex()}"/>
                        <meta name="dtb:depth" content="1"/>
                        <meta name="dtb:totalPageCount" content="0"/>
                        <meta name="dtb:maxPageNumber" content="0"/>
                    </head>
                    <docTitle>
                        <text>{title}</text>
                    </docTitle>
                    <navMap>
                        <navPoint id="navpoint-1" playOrder="1">
                            <navLabel>
                                <text>Title</text>
                            </navLabel>
                            <content src="title.xhtml"/>
                        </navPoint>
                        <navPoint id="navpoint-2" playOrder="2">
                            <navLabel>
                                <text>Content</text>
                            </navLabel>
                            <content src="content.xhtml"/>
                        </navPoint>
                    </navMap>
                </ncx>''')
            
            # Create EPUB file (ZIP with specific format)
            with zipfile.ZipFile(output_path, 'w') as epub:
                # Add mimetype first without compression
                epub.write(os.path.join(epub_temp, "mimetype"), "mimetype", 
                         compress_type=zipfile.ZIP_STORED)
                
                # Add other files with compression
                for root, dirs, files in os.walk(epub_temp):
                    for file in files:
                        if file != "mimetype":
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, epub_temp)
                            epub.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
            
            # Clean up temp directory
            import shutil
            shutil.rmtree(epub_temp)
            
            return True
        
        except Exception as e:
            raise Exception(f"EPUB conversion failed: {str(e)}")

    def convert_to_pdf(self, fb2_path, output_path):
        """Convert FB2 to PDF format"""
        try:
            # First try using external converter if available
            import subprocess
            result = subprocess.run(['fb2pdf', fb2_path, output_path], 
                                   capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                return True
        except:
            pass
        
        # Fallback method
        self.content_text.setText("Converting to PDF format...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            import tempfile
            import os
            
            # Parse FB2
            tree = ET.parse(fb2_path)
            root = tree.getroot()
            FB2_NS = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
            
            # Extract book data
            title = self.book_data.get('title', 'Unknown')
            author = self.book_data.get('author', 'Unknown')
            
            # Create HTML for conversion to PDF
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: serif; margin: 1.5em; }}
                    h1 {{ text-align: center; }}
                    h2 {{ margin-top: 2em; }}
                    .author {{ text-align: center; font-style: italic; margin-bottom: 2em; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <div class="author">by {author}</div>
            """
            
            # Extract content
            body = root.find('.//fb:body', FB2_NS)
            if body is not None:
                paragraphs = body.findall('.//fb:p', FB2_NS)
                for p in paragraphs:
                    if p is not None:
                        text = "".join(p.itertext())
                        if text:
                            html_content += f"<p>{text}</p>\n"
            
            html_content += "</body></html>"
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                html_path = f.name
            
            # Try various conversion methods
            conversion_success = False
            
            # 1. Try using PyQt's printing capabilities
            try:
                from PyQt6.QtCore import QUrl
                from PyQt6.QtGui import QPageLayout, QPageSize
                from PyQt6.QtPrintSupport import QPrinter
                from PyQt6.QtWebEngineCore import QWebEngineSettings
                from PyQt6.QtWebEngineWidgets import QWebEngineView
                
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(output_path)
                
                page_layout = QPageLayout()
                page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                printer.setPageLayout(page_layout)
                
                web = QWebEngineView()
                web.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
                web.load(QUrl.fromLocalFile(html_path))
                
                def handle_load_finished(success):
                    if success:
                        web.page().print(printer, lambda success: print(f"PDF generation: {'success' if success else 'failed'}"))
                        conversion_success = True
                    else:
                        print("Failed to load HTML")
                
                web.loadFinished.connect(handle_load_finished)
                # Wait for page to load
                QApplication.processEvents()
                
                if conversion_success:
                    return True
            except Exception as e:
                print(f"PyQt PDF generation failed: {e}")
            
            # 2. Try wkhtmltopdf if available
            try:
                result = subprocess.run(['wkhtmltopdf', html_path, output_path], 
                                      check=True, capture_output=True)
                if result.returncode == 0:
                    conversion_success = True
            except Exception as e:
                print(f"wkhtmltopdf failed: {e}")
            
            # 3. Try reportlab as a last resort
            if not conversion_success:
                try:
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    from reportlab.lib.styles import getSampleStyleSheet
                    from reportlab.platypus import SimpleDocTemplate, Paragraph
                    
                    doc = SimpleDocTemplate(output_path, pagesize=A4)
                    styles = getSampleStyleSheet()
                    story = []
                    
                    # Add title
                    story.append(Paragraph(f"<h1>{title}</h1>", styles['Title']))
                    story.append(Paragraph(f"<i>by {author}</i>", styles['Normal']))
                    
                    # Add content paragraphs
                    if body is not None:
                        paragraphs = body.findall('.//fb:p', FB2_NS)
                        for p in paragraphs:
                            if p is not None:
                                text = "".join(p.itertext())
                                if text:
                                    story.append(Paragraph(text, styles['Normal']))
                    
                    doc.build(story)
                    conversion_success = True
                except Exception as e:
                    print(f"reportlab failed: {e}")
            
            # Clean up
            try:
                os.unlink(html_path)
            except:
                pass
            
            if conversion_success:
                return True
            else:
                raise Exception("Could not find a suitable PDF conversion method")
        
        except Exception as e:
            raise Exception(f"PDF conversion failed: {str(e)}")