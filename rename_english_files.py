#!/usr/bin/env python3
"""
Script to rename English markdown files in assets/output folders.
Removes the Chinese prefix and brackets, keeping only the English name.

Example:
    From: HA-9-0015(2)  認識腎臟移植_0_[HA-9-0015(2) Understanding Kidney Transplant_0]-ENG.md
    To:   HA-9-0015(2) Understanding Kidney Transplant_0-ENG.md
"""

import os
import re
from pathlib import Path


def rename_english_files(base_dir: str = "assets/output", dry_run: bool = True):
    """
    Rename all -ENG.md files by extracting the English name from brackets.
    
    Args:
        base_dir: Base directory containing the output folders
        dry_run: If True, only show what would be renamed without actually renaming
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return
    
    # Pattern to match files ending with [...]]-ENG.md
    # Group 1: Everything before the bracket
    # Group 2: Content inside brackets (the English name)
    pattern = re.compile(r'^(.+?)_\[(.+?)\]-ENG\.md$')
    
    renamed_count = 0
    skipped_count = 0
    
    # Iterate through all subdirectories in assets/output
    for folder in base_path.iterdir():
        if not folder.is_dir():
            continue
            
        print(f"\n📁 Processing folder: {folder.name}")
        print("=" * 80)
        
        # Find all -ENG.md files in this folder
        eng_files = list(folder.glob("*-ENG.md"))
        
        for file_path in eng_files:
            filename = file_path.name
            
            # Check if filename matches the pattern with brackets
            match = pattern.match(filename)
            
            if match:
                # Extract the English name from brackets
                english_name = match.group(2)
                
                # New filename is just the English name with -ENG.md
                new_filename = f"{english_name}-ENG.md"
                new_path = file_path.parent / new_filename
                
                # Check if new filename already exists
                if new_path.exists() and new_path != file_path:
                    print(f"⚠️  SKIP: {filename}")
                    print(f"    Target already exists: {new_filename}")
                    skipped_count += 1
                    continue
                
                print(f"✓ {filename}")
                print(f"  → {new_filename}")
                
                if not dry_run:
                    try:
                        file_path.rename(new_path)
                        renamed_count += 1
                    except Exception as e:
                        print(f"  ❌ Error renaming: {e}")
                else:
                    renamed_count += 1
            else:
                # File doesn't match the bracket pattern (might already be renamed or different format)
                print(f"ℹ️  No brackets found (skipping): {filename}")
                skipped_count += 1
    
    print("\n" + "=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Files to rename: {renamed_count}")
    print(f"   Files skipped: {skipped_count}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - No files were actually renamed")
        print(f"   Run with dry_run=False to perform actual renaming")
    else:
        print(f"\n✅ Renaming complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rename English markdown files by extracting names from brackets"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually rename files (default is dry-run mode)"
    )
    parser.add_argument(
        "--base-dir",
        default="assets/output",
        help="Base directory containing output folders (default: assets/output)"
    )
    
    args = parser.parse_args()
    
    # Run in dry-run mode by default, unless --execute is specified
    rename_english_files(
        base_dir=args.base_dir,
        dry_run=not args.execute
    )
