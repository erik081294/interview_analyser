import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
AI_MODEL = "claude-3-5-haiku-20241022"  # Correcte model naam voor Claude-3

# File Processing
ALLOWED_EXTENSIONS = {'.txt', '.doc', '.docx', '.pdf'}
MAX_FILE_SIZE_MB = 10
CHUNK_SIZE = 2000  # characters per chunk for processing

# Analysis Settings
DEFAULT_LANGUAGE = 'nl'  # Dutch
SENTIMENT_ANALYSIS = True
PATTERN_RECOGNITION = True
MINIMUM_STATEMENT_LENGTH = 10
MAXIMUM_STATEMENT_LENGTH = 750

# Visualization
MAX_WORDCLOUD_WORDS = 100
NETWORK_GRAPH_MIN_EDGE_WEIGHT = 2

# Storage
DATA_DIR = 'data'
TEMP_DIR = 'temp'
EXPORT_DIR = 'exports'

# Create necessary directories if they don't exist
for directory in [DATA_DIR, TEMP_DIR, EXPORT_DIR]:
    os.makedirs(directory, exist_ok=True) 