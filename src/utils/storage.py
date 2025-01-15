import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from ..models import Interview, Statement, StatementType
from ..config import DATA_DIR

def save_interview(interview: Interview) -> bool:
    """Save interview to local storage."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Convert interview to serializable format
        interview_data = {
            'interviewee': interview.interviewee,
            'date': datetime.now().isoformat(),
            'raw_text': interview.raw_text,
            'statements': [
                {
                    'text': s.text,
                    'type': s.type.value,
                    'source_text': s.source_text,
                    'confidence': s.confidence,
                    'metadata': s.metadata
                }
                for s in interview.statements
            ],
            'metadata': interview.metadata,
            'ready_for_analysis': interview.metadata.get('ready_for_analysis', False)
        }
        
        # Save to file
        filename = interview.metadata.get('filename') or f"{interview.interviewee}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(interview_data, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        print(f"Error saving interview: {str(e)}")
        return False

def save_analysis_version(analysis_text: str, questions: List[str], metadata: Dict) -> str:
    """Save a version of the analysis and return its filename."""
    try:
        # Create versions directory
        versions_dir = os.path.join(DATA_DIR, 'analysis_versions')
        os.makedirs(versions_dir, exist_ok=True)
        
        # Create version data
        version_data = {
            'text': analysis_text,
            'questions': questions,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat(),
            'version_type': metadata.get('version_type', 'manual')  # manual, ai_chat, or initial
        }
        
        # Generate filename
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(versions_dir, filename)
        
        # Save version
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    except Exception as e:
        print(f"Error saving analysis version: {str(e)}")
        return None

def load_analysis_versions() -> List[Dict]:
    """Load all analysis versions, sorted by timestamp."""
    versions = []
    versions_dir = os.path.join(DATA_DIR, 'analysis_versions')
    
    try:
        if not os.path.exists(versions_dir):
            return versions
        
        for filename in os.listdir(versions_dir):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(versions_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                version_data['filename'] = filename
                versions.append(version_data)
        
        # Sort by timestamp, newest first
        versions.sort(key=lambda x: x['timestamp'], reverse=True)
        return versions
    
    except Exception as e:
        print(f"Error loading analysis versions: {str(e)}")
        return versions

def get_latest_analysis_version() -> Optional[Dict]:
    """Get the most recent analysis version."""
    versions = load_analysis_versions()
    return versions[0] if versions else None

def load_interviews() -> List[Interview]:
    """Load all interviews from local storage."""
    interviews = []
    
    try:
        if not os.path.exists(DATA_DIR):
            return interviews
        
        # Only process files in the root directory, not in subdirectories
        for filename in [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]:
            if not filename.endswith('.json') or filename.startswith('analysis_'):
                continue
            
            filepath = os.path.join(DATA_DIR, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Verify this is an interview file by checking required fields
                if not all(key in data for key in ['interviewee', 'statements']):
                    continue
                
                # Convert statements back to objects
                statements = [
                    Statement(
                        text=s['text'],
                        type=StatementType(s['type']),
                        source_text=s['source_text'],
                        confidence=s['confidence'],
                        metadata=s.get('metadata', {})
                    )
                    for s in data['statements']
                ]
                
                # Create interview object
                interview = Interview(
                    interviewee=data['interviewee'],
                    date=datetime.fromisoformat(data['date']),
                    raw_text=data['raw_text'],
                    statements=statements,
                    metadata=data.get('metadata', {})
                )
                
                # Add filename to metadata for deletion
                interview.metadata['filename'] = filename
                interview.metadata['ready_for_analysis'] = data.get('ready_for_analysis', False)
                
                interviews.append(interview)
            except Exception as e:
                print(f"Error loading interview {filename}: {str(e)}")
                continue
        
        return interviews
    
    except Exception as e:
        print(f"Error loading interviews: {str(e)}")
        return interviews

def delete_interview(filename: str) -> bool:
    """Delete an interview file from local storage."""
    try:
        print(f"\n=== Starting deletion process for: {filename} ===")
        
        # Get full path
        filepath = os.path.join(DATA_DIR, filename)
        print(f"Full filepath: {filepath}")
        print(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}")
        print(f"Current files in DATA_DIR: {os.listdir(DATA_DIR)}")
        
        # Safety checks
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False
        
        if not os.path.isfile(filepath):
            print(f"❌ Not a file: {filepath}")
            return False
            
        if not filename.endswith('.json') or filename.startswith('analysis_'):
            print(f"❌ Not an interview file: {filepath}")
            return False
        
        try:
            # Verify it's an interview file by checking its contents
            print("Reading file contents...")
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not all(key in data for key in ['interviewee', 'statements']):
                    print(f"❌ Not a valid interview file: {filepath}")
                    print(f"Found keys: {list(data.keys())}")
                    return False
                print("✓ Valid interview file format")
        except Exception as e:
            print(f"❌ Error verifying interview file: {str(e)}")
            return False
        
        # Remove file
        print(f"Attempting to remove file: {filepath}")
        os.remove(filepath)
        
        # Verify file is gone
        if os.path.exists(filepath):
            print(f"❌ File still exists after deletion attempt: {filepath}")
            return False
            
        print(f"✓ Successfully deleted interview file: {filepath}")
        print(f"Remaining files in DATA_DIR: {os.listdir(DATA_DIR)}")
        return True
    
    except Exception as e:
        print(f"❌ Error in delete_interview: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def mark_for_analysis(filename: str, ready: bool = True) -> bool:
    """Mark or unmark an interview as ready for analysis."""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            return False
        
        # Load existing data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update ready_for_analysis flag
        data['ready_for_analysis'] = ready
        
        # Save updated data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        print(f"Error updating interview: {str(e)}")
        return False 