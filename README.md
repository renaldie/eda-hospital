# Document Processing Pipeline

## OCR
run `ocr-pipeline.ipynb`
input: ./assets/input
output: ./assets/output-zh-ocr

## Chinese
Folders are:
- `./assets/output-zh-ocr`
- `./assets/output-zh-combined`

### Convert HTML Table
run `uv run process_html_table.py --input_dir "./assets/output-zh-ocr" --output_dir "./assets/output-zh-combined"`

### Combine MD Files
run `uv run combine_multipage_files.py --execute --input_dir "./assets/output-zh-combined" --output_dir "./assets/output-zh-combined"`

## Build VectorDB
run `uv run build_vectordb.py --execute --collection_name "eda-hospital-zh" --persist_directory "./vectordb/eda-hospital-zh" --input_dir "./assets/output-zh-combined"`

## English
Folders are:
- `./assets/output-en-ocr`
- `./assets/output-en-combined`

### Build Translated File Names Dict
run `build_filename.py --input_dir "./assets/output-zh-ocr" --json_path "./filename_translation.json"`

### Translate and Convert HTML Table
run `uv run translate_file_content.py --input_dir "./assets/output-zh-ocr" --output_dir "./assets/output-en-ocr"`

### Combine MD Files
run `uv run combine_multipage_files.py --execute --input_dir "./assets/output-en-ocr" --output_dir "./assets/output-en-combined"`

## Rename Combined MD Files
ru `uv run rename_files.py --execute --json_file "./filename_translation.json"--target_dir "./assets/output-en-combined"`

## Build VectorDB
run `uv run build_vectordb.py --execute --collection_name "eda-hospital-en" --persist_directory "./vectordb/eda-hospital-en" --input_dir "./assets/output-end-combined"`