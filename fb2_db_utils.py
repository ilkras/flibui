#!/usr/bin/env python3

import sqlite3
import csv
import os
from pathlib import Path
import zipfile
import tempfile
import hashlib
import xml.etree.ElementTree as ET

# Set namespaces for FB2 format
FB2_NS = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

def initialize_database(db_path):
    """Create the database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create main table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fb2_files (
        id INTEGER PRIMARY KEY,
        outer_zip TEXT NOT NULL,
        inner_zip TEXT NOT NULL,
        sha1 TEXT NOT NULL,
        title TEXT,
        author TEXT,
        year TEXT,
        publisher TEXT,
        size INTEGER,
        UNIQUE(sha1),
        UNIQUE(outer_zip, inner_zip)
    )
    ''')
    
    # Create FTS virtual table
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS fb2_search USING fts5(
        title, 
        author, 
        publisher,
        content='fb2_files',
        content_rowid='id',
        tokenize='unicode61'
    )
    ''')
    
    # Create triggers to keep FTS updated
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS fb2_files_ai AFTER INSERT ON fb2_files BEGIN
        INSERT INTO fb2_search(rowid, title, author, publisher)
        VALUES (new.id, new.title, new.author, new.publisher);
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS fb2_files_au AFTER UPDATE ON fb2_files BEGIN
        INSERT INTO fb2_search(fb2_search, rowid, title, author, publisher)
        VALUES('delete', old.id, old.title, old.author, old.publisher);
        INSERT INTO fb2_search(rowid, title, author, publisher)
        VALUES (new.id, new.title, new.author, new.publisher);
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS fb2_files_ad AFTER DELETE ON fb2_files BEGIN
        INSERT INTO fb2_search(fb2_search, rowid, title, author, publisher)
        VALUES('delete', old.id, old.title, old.author, old.publisher);
    END;
    ''')
    
    conn.commit()
    return conn

def calculate_sha1(file_path):
    """Calculate SHA1 hash of a file."""
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha1.update(chunk)
    return sha1.hexdigest()

def extract_fb2_metadata(fb2_path):
    """Extract metadata from FB2 file."""
    try:
        tree = ET.parse(fb2_path)
        root = tree.getroot()
        
        # Initialize with default values
        author = "unknown"
        title = "unknown"
        year = "unknown"
        publisher = "unknown"
        
        # Extract title
        title_element = root.find('.//fb:book-title', FB2_NS)
        if title_element is not None and title_element.text:
            title = title_element.text.strip()
        
        # Extract author
        author_element = root.find('.//fb:author', FB2_NS)
        if author_element is not None:
            first_name = author_element.find('.//fb:first-name', FB2_NS)
            last_name = author_element.find('.//fb:last-name', FB2_NS)
            
            author_parts = []
            if first_name is not None and first_name.text:
                author_parts.append(first_name.text.strip())
            if last_name is not None and last_name.text:
                author_parts.append(last_name.text.strip())
            
            if author_parts:
                author = " ".join(author_parts)
        
        # Extract year and publisher from publish-info
        publish_info = root.find('.//fb:publish-info', FB2_NS)
        if publish_info is not None:
            year_element = publish_info.find('.//fb:year', FB2_NS)
            if year_element is not None and year_element.text:
                year = year_element.text.strip()
            
            publisher_element = publish_info.find('.//fb:publisher', FB2_NS)
            if publisher_element is not None and publisher_element.text:
                publisher = publisher_element.text.strip()
        
        return {
            'author': author,
            'title': title,
            'year': year,
            'publisher': publisher
        }
    except Exception as e:
        print(f"Error parsing FB2 file {fb2_path}: {e}")
        return {
            'author': "unknown",
            'title': "unknown",
            'year': "unknown",
            'publisher': "unknown"
        }

def get_processed_archives(conn):
    """Get list of already processed archive filenames."""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT outer_zip FROM fb2_files")
    return {row[0] for row in cursor.fetchall()}

def process_archive(conn, archive_path, temp_dir):
    """Process a single archive and add its contents to the database."""
    cursor = conn.cursor()
    inserted_count = 0
    
    try:
        outer_zip_path = Path(archive_path)
        outer_zip_name = outer_zip_path.name
        print(f"Processing archive: {outer_zip_name}")
        
        with zipfile.ZipFile(archive_path, 'r') as outer_zip:
            fb2_files = [f for f in outer_zip.namelist() if f.lower().endswith('.fb2')]
            print(f"  Found {len(fb2_files)} FB2 files")
            
            for fb2_name in fb2_files:
                # Check if this specific file is already in the database
                cursor.execute(
                    "SELECT id FROM fb2_files WHERE outer_zip = ? AND inner_zip = ?", 
                    (outer_zip_name, fb2_name)
                )
                if cursor.fetchone():
                    print(f"  Skipping already imported: {fb2_name}")
                    continue
                    
                fb2_path = os.path.join(temp_dir, "book.fb2")
                
                # Extract FB2 file
                with open(fb2_path, 'wb') as f:
                    f.write(outer_zip.read(fb2_name))
                
                # Get file size
                size = os.path.getsize(fb2_path)
                
                # Calculate SHA1
                sha1 = calculate_sha1(fb2_path)
                
                # Check if we already have this file with a different name
                cursor.execute("SELECT id FROM fb2_files WHERE sha1 = ?", (sha1,))
                if cursor.fetchone():
                    print(f"  Skipping duplicate content: {fb2_name} (SHA1: {sha1})")
                    continue
                
                # Extract metadata
                metadata = extract_fb2_metadata(fb2_path)
                
                # Insert into database
                try:
                    cursor.execute('''
                    INSERT INTO fb2_files 
                    (outer_zip, inner_zip, sha1, author, size, title, year, publisher)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (outer_zip_name, fb2_name, sha1, metadata['author'], 
                         size, metadata['title'], metadata['year'], metadata['publisher']))
                    inserted_count += 1
                    print(f"  Added: {fb2_name}")
                except sqlite3.IntegrityError as e:
                    print(f"  Skipping (database constraint): {fb2_name} - {e}")
    
    except zipfile.BadZipFile:
        print(f"Error: {archive_path} is not a valid zip file")
    
    conn.commit()
    return inserted_count