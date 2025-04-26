
# FB2 Database Manager

A Python application for managing FB2 (FictionBook) ebook collections. This tool creates and maintains a searchable SQLite database of your ebook collection's metadata while keeping the actual files in their original archives.

## Features

- **Command-line tools** for scanning archives and building database
- **Graphical user interface** for searching and managing books
- **Full-text search** with partial matching
- **Book preview** with content extraction
- **Format conversion** to EPUB and PDF
- **Duplicate detection** to prevent redundant entries
- **Large collection support** with efficient database design

## Installation

### Required Packages (Linux)

1. **Python 3.6 or newer**
   ```bash
   sudo apt install python3
   ```

2. **PyQt6 (for the GUI)**
   ```bash
   sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine
   ```

3. **SQLite**
   ```bash
   sudo apt install sqlite3
   ```

### Optional Dependencies for Enhanced Functionality

1. **PDF Conversion Tools**
   ```bash
   sudo apt install wkhtmltopdf
   ```

2. **Additional Python Modules for Improved Conversion**
   ```bash
   sudo apt install python3-reportlab
   ```

### Setting Up

1. Place all script files in your working directory:
   - `fb2_db_utils.py` - Shared utility functions
   - `fb2_db_manager.py` - Command-line database manager
   - `fb2_gui_app.py` - GUI application
   - `fb2_gui_ui.py` - UI definition for GUI
   - `fb2_book_dialog.py` - Book details dialog

2. Make the scripts executable:
   ```bash
   chmod +x fb2_db_manager.py fb2_gui_app.py
   ```

## Usage: Command-Line Tools

### Creating a new database

Create a new database by scanning a directory of archives:

```bash
python3 fb2_db_manager.py create /path/to/archives --db fb2_catalog.db
```

Options:
- `--force` - Process all archives, even if previously processed
- `--db` - Specify database file path (default: fb2_catalog.db)

### Updating an existing database

Add new archives to an existing database:

```bash
python3 fb2_db_manager.py update /path/to/archives --db fb2_catalog.db
```

### Importing from CSV (Legacy)

If you have existing metadata in CSV format:

```bash
python3 fb2_db_manager.py import-csv metadata.csv --db fb2_catalog.db
```

The CSV should have the following columns:
- outer_zip (archive filename)
- inner_zip (file path within archive)
- sha1 (file hash)
- author
- size (in bytes)
- title
- year
- publisher

## Usage: Graphical User Interface

Launch the GUI application:

```bash
python3 fb2_gui_app.py
```

### GUI Features

1. **Database Management**
   - Create a new database (File → Create New Database)
   - Open an existing database (File → Open Database)
   - Process archives to add to database (Select Directory button)

2. **Book Search**
   - Enter search terms to find matching books
   - Results show book metadata in a sortable table
   - Double-click on a result to view book details

3. **Book Details**
   - View book metadata
   - Read content preview/annotation
   - Extract book in multiple formats:
     - FB2 (original format)
     - EPUB (converted)
     - PDF (converted)

4. **Format Conversion**
   - Built-in FB2 to EPUB converter
   - Built-in FB2 to PDF converter with multiple fallback methods
   - Uses external tools if available for better quality

## Database Structure

The tool creates an SQLite database with:

1. Main table `fb2_files` containing:
   - Archive filename
   - Path within archive
   - SHA1 hash
   - Metadata (author, title, year, publisher)
   - File size

2. Full-text search virtual table `fb2_search` for efficient text searching

## Common Use Cases

### Processing a collection for the first time

```bash
python3 fb2_db_manager.py create /media/user/books/fb2 --db my_books.db
```

### Adding new books to your collection

```bash
python3 fb2_db_manager.py update /media/user/books/fb2 --db my_books.db
```

### Re-scanning the entire collection

```bash
python3 fb2_db_manager.py create /media/user/books/fb2 --force --db my_books.db
```

### Searching with the GUI

1. Launch the GUI: `python3 fb2_gui_app.py`
2. Open your database file (File → Open Database)
3. Enter search terms in the search box
4. Browse results and double-click to view details
5. Use the Extract button to save books in your preferred format

## Querying the Database

Once your database is created, you can use SQLite tools:

```bash
sqlite3 fb2_catalog.db
```

Sample queries:
```sql
-- Count total books
SELECT COUNT(*) FROM fb2_files;

-- Find books by author (partial match)
SELECT * FROM fb2_files WHERE author LIKE '%Tolkien%';

-- Use full-text search
SELECT fb2_files.* FROM fb2_search 
JOIN fb2_files ON fb2_search.rowid = fb2_files.id
WHERE fb2_search MATCH 'hobbit';
```

## Troubleshooting

- **PDF/EPUB conversion fails**: Install additional conversion tools
- **PyQt modules not found**: Ensure PyQt6 is properly installed
- **Archives not found**: Check that the archive path is correctly specified
- **Database errors**: Check SQLite version and file permissions
- **Error opening archive**: Ensure the ZIP file is valid
- **No files found**: Verify that files have .fb2 extension
- **Database locked**: Close other applications using the database

## File Structure

```
fb2_db_utils.py    - Core database and archive processing functions
fb2_db_manager.py  - Command-line interface for database management
fb2_gui_app.py     - Main GUI application
fb2_gui_ui.py      - GUI layout definitions
fb2_book_dialog.py - Book details and extraction dialog
```

## License

This software is provided as-is for personal use.
