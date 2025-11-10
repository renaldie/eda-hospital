#!/usr/bin/env python3
"""
Script to rename markdown files using a JSON mapping file.

Example:
    JSON file contains: {"old_name": "new_name", ...}
    Renames: old_name.md -> new_name.md
"""

import os
import json
from pathlib import Path


def rename_files(json_file: str, target_dir: str, dry_run: bool = True):
    """
    Rename all .md files using mappings from a JSON file.
    
    Args:
        json_file: Path to the JSON file containing filename mappings
        target_dir: Target directory containing the folders with markdown files
        dry_run: If True, only show what would be renamed without actually renaming
    """
    json_path = Path(json_file)
    target_path = Path(target_dir)
    
    if not json_path.exists():
        print(f"Error: JSON file {json_file} does not exist")
        return
    
    if not target_path.exists():
        print(f"Error: Directory {target_dir} does not exist")
        return
    
    # Load the filename mapping
    with open(json_path) as f:
        filename_mapping = json.load(f)
    
    renamed_count = 0
    skipped_count = 0
    
    # Iterate through all subdirectories
    for folder in os.listdir(target_dir):
        folder_path = target_path / folder
        
        if not folder_path.is_dir():
            continue
        
        print(f"\n📁 Processing folder: {folder}")
        print("=" * 80)
        
        # Process all .md files in this folder
        for file in os.listdir(folder_path):
            if not file.endswith(".md"):
                continue
            
            basename = os.path.splitext(file)[0]
            
            # Check if this basename has a mapping
            if basename not in filename_mapping:
                print(f"⚠️  No mapping found for: {file}")
                skipped_count += 1
                continue
            
            new_basename = filename_mapping[basename]
            new_filename = f"{new_basename}.md"
            
            src_path = folder_path / file
            dst_path = folder_path / new_filename
            
            # Check if new filename already exists
            if dst_path.exists() and dst_path != src_path:
                print(f"⚠️  SKIP: {file}")
                print(f"    Target already exists: {new_filename}")
                skipped_count += 1
                continue
            
            print(f"✓ Old name: {file}")
            print(f"  New name: {new_filename}")
            
            if not dry_run:
                try:
                    os.rename(src_path, dst_path)
                    renamed_count += 1
                except Exception as e:
                    print(f"  ❌ Error renaming: {e}")
                    skipped_count += 1
            else:
                renamed_count += 1
    
    print("\n" + "=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Files to rename: {renamed_count}")
    print(f"   Files skipped: {skipped_count}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - No files were actually renamed")
        print(f"   Run with --execute to perform actual renaming")
    else:
        print(f"\n✅ Renaming complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rename markdown files using a JSON mapping file"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rename files (default is dry-run mode)"
    )
    parser.add_argument(
        "--json_file",
        required=True,
        help="Path to the JSON file containing filename mappings"
    )
    parser.add_argument(
        "--target_dir",
        required=True,
        help="Target directory containing folders with markdown files"
    )
    
    args = parser.parse_args()
    
    # Run in dry-run mode by default, unless --execute is specified
    rename_files(
        json_file=args.json_file,
        target_dir=args.target_dir,
        dry_run=not args.execute
    )

