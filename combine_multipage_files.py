#!/usr/bin/env python3
"""
Script to combine multi-page markdown files in assets/output folders.
Files with the same base name but different page numbers (_0, _1, etc.) will be merged.

Example:
    From: HA-9-0061(3)健康檢查前注意事項_0.md
          HA-9-0061(3)健康檢查前注意事項_1.md
    To:   HA-9-0061(3)健康檢查前注意事項.md
"""

import os
import re
import shutil
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
    # Pattern to match _<number> before the .md extension
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
    
    # Return all groups (including single files)
    return grouped


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


def combine_multipage_files(input_dir: str, 
                            output_dir: str,
                            dry_run: bool = True,
                            add_page_separator: bool = False):
    """
    Combine multi-page markdown files into single files.
    
    Args:
        input_dir: Input directory containing the markdown files with page numbers
        output_dir: Output directory where combined files will be saved
        dry_run: If True, only show what would be done without actually doing it
        add_page_separator: Whether to add "---" separator between pages
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist")
        return
    
    if not dry_run and not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    total_groups = 0
    total_files_combined = 0
    
    # Iterate through all subdirectories in input directory
    for folder in input_path.iterdir():
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
        
        # Create corresponding output subfolder
        output_subfolder = output_path / folder.name
        if not dry_run:
            output_subfolder.mkdir(parents=True, exist_ok=True)
            
            # Copy all subdirectories (like imgs/) from input to output
            for item in folder.iterdir():
                if item.is_dir():
                    dest_dir = output_subfolder / item.name
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(item, dest_dir)
                    print(f"   📂 Copied directory: {item.name}/")
        else:
            # Show what directories would be copied in dry-run mode
            subdirs = [item.name for item in folder.iterdir() if item.is_dir()]
            if subdirs:
                print(f"   📂 Directories to copy: {', '.join(subdirs)}")
        
        # Process each group
        for base_name, file_group in grouped_files.items():
            total_groups += 1
            num_pages = len(file_group)
            total_files_combined += num_pages
            
            output_file_path = output_subfolder / base_name
            
            if num_pages == 1:
                print(f"\n✓ Copying single file:")
                print(f"  → Output: {output_file_path}")
                print(f"     Source: {file_group[0][0].name}")
            else:
                print(f"\n✓ Combining {num_pages} pages:")
                print(f"  → Output: {output_file_path}")
                
                for file_path, page_num in file_group:
                    print(f"     Page {page_num}: {file_path.name}")
            
            if not dry_run:
                try:
                    # Combine files (or copy single file)
                    combine_files(file_group, output_file_path, add_page_separator)
                    print(f"  ✅ {'Copied' if num_pages == 1 else 'Combined'} successfully")
                    
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
        print(f"\n✅ Combining complete!")
        print(f"   Original files kept in: {input_dir}")
        print(f"   Combined files saved to: {output_dir}")


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
        "--input-dir",
        required=True,
        help="Input directory containing markdown files with page numbers"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory where combined files will be saved"
    )
    parser.add_argument(
        "--add-separator",
        action="store_true",
        help="Add '---' separator between pages in combined file"
    )
    
    args = parser.parse_args()
    
    # Run in dry-run mode by default, unless --execute is specified
    combine_multipage_files(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        dry_run=not args.execute,
        add_page_separator=args.add_separator
    )
