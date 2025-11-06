#!/usr/bin/env python3
"""
Script to combine multi-page Chinese markdown files in assets/output folders.
Files with the same base name but different page numbers (_0, _1, etc.) will be merged.
Only combines original Chinese markdown files (not English translations with -ENG suffix).

Example:
    From: HA-9-0061(3)健康檢查前注意事項_0.md
          HA-9-0061(3)健康檢查前注意事項_1.md
    To:   HA-9-0061(3)健康檢查前注意事項.md
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def get_base_name(filename: str) -> tuple[str, int]:
    """
    Extract base name and page number from filename.
    
    Args:
        filename: The filename to parse
        
    Returns:
        Tuple of (base_name, page_number)
        Example: "HA-9-0061(3)健康檢查前注意事項_0.md" -> ("HA-9-0061(3)健康檢查前注意事項.md", 0)
                 "HA-9-0061(3)健康檢查前注意事項_1.md" -> ("HA-9-0061(3)健康檢查前注意事項.md", 1)
    """
    # Skip English translated files
    if filename.endswith('-ENG.md'):
        return (filename, -1)
    
    # Pattern to match _<number> before the .md extension (for Chinese files only)
    pattern = r'^(.+?)_(\d+)\.md$'
    match = re.match(pattern, filename)
    
    if match:
        base = match.group(1)
        page_num = int(match.group(2))
        base_name = f"{base}.md"
        return (base_name, page_num)
    
    return (filename, -1)  # Return -1 if no page number found


def group_files_by_base(files: List[Path]) -> Dict[str, List[tuple[Path, int]]]:
    """
    Group files by their base name.
    
    Returns:
        Dictionary mapping base_name -> list of (file_path, page_number) tuples
    """
    grouped = defaultdict(list)
    
    for file_path in files:
        if file_path.name.endswith('.md'):
            base_name, page_num = get_base_name(file_path.name)
            
            # Only group files that have page numbers (_0, _1, etc.)
            if page_num >= 0:
                grouped[base_name].append((file_path, page_num))
    
    # Sort each group by page number
    for base_name in grouped:
        grouped[base_name].sort(key=lambda x: x[1])
    
    # Only return groups with multiple files
    return {k: v for k, v in grouped.items() if len(v) > 1}


def combine_files(file_group: List[tuple[Path, int]], output_path: Path, 
                  add_page_separator: bool = True) -> None:
    """
    Combine multiple files into one.
    
    Args:
        file_group: List of (file_path, page_number) tuples
        output_path: Path where the combined file will be saved
        add_page_separator: Whether to add separator between pages
    """
    combined_content = []
    
    for i, (file_path, page_num) in enumerate(file_group):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Add page separator if not the first page
        if i > 0 and add_page_separator:
            combined_content.append(f"\n\n---\n\n")
        
        combined_content.append(content)
    
    # Write combined content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(combined_content))


def combine_multipage_files(base_dir: str = "assets/output", 
                            dry_run: bool = True,
                            add_page_separator: bool = False,
                            delete_originals: bool = True):
    """
    Combine multi-page markdown files into single files.
    
    Args:
        base_dir: Base directory containing the output folders
        dry_run: If True, only show what would be done without actually doing it
        add_page_separator: Whether to add "---" separator between pages
        delete_originals: Whether to delete original files after combining
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return
    
    total_groups = 0
    total_files_combined = 0
    total_files_deleted = 0
    
    # Iterate through all subdirectories in assets/output
    for folder in base_path.iterdir():
        if not folder.is_dir():
            continue
        
        print(f"\n📁 Processing folder: {folder.name}")
        print("=" * 80)
        
        # Get all .md files in this folder
        md_files = list(folder.glob("*.md"))
        
        # Group files by base name
        grouped_files = group_files_by_base(md_files)
        
        if not grouped_files:
            print("   No multi-page files found")
            continue
        
        # Process each group
        for base_name, file_group in grouped_files.items():
            total_groups += 1
            num_pages = len(file_group)
            total_files_combined += num_pages
            
            output_path = folder / base_name
            
            print(f"\n✓ Combining {num_pages} pages:")
            print(f"  → Output: {base_name}")
            
            for file_path, page_num in file_group:
                print(f"     Page {page_num}: {file_path.name}")
            
            if not dry_run:
                try:
                    # Combine files
                    combine_files(file_group, output_path, add_page_separator)
                    
                    # Delete original files if requested
                    if delete_originals:
                        for file_path, _ in file_group:
                            file_path.unlink()
                            total_files_deleted += 1
                    
                    print(f"  ✅ Combined successfully")
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print(f"\n📊 Summary:")
    print(f"   File groups combined: {total_groups}")
    print(f"   Total files processed: {total_files_combined}")
    
    if dry_run:
        print(f"\n⚠️  DRY RUN MODE - No files were actually combined")
        print(f"   Run with --execute to perform actual combining")
    else:
        if delete_originals:
            print(f"   Original files deleted: {total_files_deleted}")
        print(f"\n✅ Combining complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Combine multi-page markdown files into single files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually combine files (default is dry-run mode)"
    )
    parser.add_argument(
        "--base-dir",
        required=True,
        help="Base directory containing output folders (default: assets/output)"
    )
    parser.add_argument(
        "--add-separator",
        action="store_true",
        help="Add '---' separator between pages in combined file"
    )
    parser.add_argument(
        "--keep-originals",
        action="store_true",
        help="Keep original files after combining (default is to delete them)"
    )
    
    args = parser.parse_args()
    
    # Run in dry-run mode by default, unless --execute is specified
    combine_multipage_files(
        base_dir=args.base_dir,
        dry_run=not args.execute,
        add_page_separator=args.add_separator,
        delete_originals=not args.keep_originals
    )
