import os
from typing import Union, BinaryIO
import docx
import pdfplumber
from ..config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB

def validate_file(file: Union[str, BinaryIO]) -> bool:
    """Validate if the file is allowed and within size limits."""
    if isinstance(file, str):
        file_ext = os.path.splitext(file)[1].lower()
    else:
        # For uploaded files through Streamlit
        file_ext = os.path.splitext(file.name)[1].lower()
        
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size
    if isinstance(file, str):
        size_mb = os.path.getsize(file) / (1024 * 1024)
    else:
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
    
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB")
    
    return True

def read_text_file(file_path: str) -> str:
    """Read content from a text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_docx_file(file_path: str) -> str:
    """Read content from a Word document."""
    doc = docx.Document(file_path)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

def read_pdf_file(file_path: str) -> str:
    """Read content from a PDF file."""
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or '')
    return '\n'.join(text)

def read_file_content(file: Union[str, BinaryIO]) -> str:
    """Read content from any supported file type."""
    validate_file(file)
    
    if isinstance(file, str):
        file_path = file
    else:
        # For uploaded files, save temporarily
        temp_path = f"temp/{file.name}"
        os.makedirs('temp', exist_ok=True)
        with open(temp_path, 'wb') as f:
            f.write(file.read())
        file_path = temp_path
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.txt':
            content = read_text_file(file_path)
        elif file_ext in ['.doc', '.docx']:
            content = read_docx_file(file_path)
        elif file_ext == '.pdf':
            content = read_pdf_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Clean up temp file if needed
        if not isinstance(file, str):
            os.remove(temp_path)
            
        return content
    
    except Exception as e:
        if not isinstance(file, str) and os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"Error reading file: {str(e)}") 