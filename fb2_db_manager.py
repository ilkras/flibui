#!/usr/bin/env python3

import argparse
import os
import tempfile
from pathlib import Path
import sqlite3

from fb2_db_utils import (
    initialize_database, 
    process_archive, 
    get_processed_archives,
    calculate_sha1
)

def create_db(db_path, csv_path):
    """Create a new database from CSV file."""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file {csv_path} not found")
        return False
    
    conn = initialize_database(db_path)
    cursor = conn.cursor()
    
    # Import CSV data
    print(f"Importing data from {csv_path}...")
    records_added = 0
    
    with open(csv_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        # Skip header row if it exists
        try:
            header = next(csv_reader)
            if len(header) < 8:  # Simple validation
                print("Warning: CSV header row may be missing or invalid")
        except StopIteration:
            print(f"Error: CSV file {csv_path} appears to be empty")
            conn.close()
            return False
        
        for row in csv_reader:
            try:
                if len(row) < 8:
                    print(f"Skipping invalid row (not enough columns): {row}")
                    continue
                
                outer_zip, inner_zip, sha1, author, size, title, year, publisher = row
                
                # Try to convert size to integer
                try:
                    size = int(size)
                except (ValueError, TypeError):
                    size = 0
                
                cursor.execute('''
                INSERT INTO fb2_files 
                (outer_zip, inner_zip, sha1, author, size, title, year, publisher)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (outer_zip, inner_zip, sha1, author, size, title, year, publisher))
                records_added += 1
                
                if records_added % 10000 == 0:
                    print(f"Processed {records_added} records...")
                    conn.commit()
                    
            except Exception as e:
                print(f"Error importing row {row}: {e}")
    
    conn.commit()
    print(f"Import completed. Added {records_added} records to the database.")
    
    # Show some stats
    cursor.execute("SELECT COUNT(*) FROM fb2_files")
    count = cursor.fetchone()[0]
    print(f"Database now contains {count} FB2 files")
    
    conn.close()
    return True

def process_archives(db_path, archives_dir, force_reprocess=False):
    """Process archives and add to database."""
    if not os.path.isdir(archives_dir):
        print(f"Error: Directory {archives_dir} not found")
        return False
    
    conn = initialize_database(db_path)
    
    # Get already processed archives if not forcing reprocessing
    processed_archives = set()
    if not force_reprocess:
        processed_archives = get_processed_archives(conn)
    
    # Find ZIP files in the directory
    archives = [f for f in Path(archives_dir).glob('*.zip')]
    print(f"Found {len(archives)} archives in directory")
    
    # Process only new archives unless force_reprocess is True
    if force_reprocess:
        new_archives = archives
        print(f"Processing all {len(new_archives)} archives (force mode)")
    else:
        new_archives = [a for a in archives if a.name not in processed_archives]
        print(f"Processing {len(new_archives)} new archives")
    
    total_inserted = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        for archive in new_archives:
            inserted = process_archive(conn, archive, temp_dir)
            total_inserted += inserted
    
    print(f"Added {total_inserted} new FB2 files to the database")
    conn.close()
    return True

def main():
    parser = argparse.ArgumentParser(description='FB2 Book Database Manager')
    parser.add_argument('--db', help='Path to database file', default='fb2_catalog.db')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    subparsers.required = True
    
    # Create database command
    create_parser = subparsers.add_parser('create', help='Create new database from archives')
    create_parser.add_argument('archives_dir', help='Directory containing FB2 archives')
    create_parser.add_argument('--force', action='store_true', help='Force processing of all archives')
    
    # Update database command
    update_parser = subparsers.add_parser('update', help='Update database with new archives')
    update_parser.add_argument('archives_dir', help='Directory containing FB2 archives')
    
    # Import from CSV (kept for backward compatibility)
    import_parser = subparsers.add_parser('import-csv', help='Import records from CSV file')
    import_parser.add_argument('csv_file', help='Path to CSV file with FB2 metadata')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        # For create, we force processing of all archives
        process_archives(args.db, args.archives_dir, force_reprocess=args.force)
    elif args.command == 'update':
        # For update, we only process new archives
        process_archives(args.db, args.archives_dir, force_reprocess=False)
    elif args.command == 'import-csv':
        # Keep the CSV import functionality for backward compatibility
        create_db(args.db, args.csv_file)

if __name__ == "__main__":
    main()