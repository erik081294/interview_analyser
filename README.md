# AI Interview Analysis Tool

A powerful tool for analyzing and extracting insights from interview transcripts using AI.

## Features

- Interview text processing and statement extraction
- Multi-format file support (.txt, .doc, .pdf)
- AI-powered analysis and insights generation
- Interactive visualizations and reporting
- Statement categorization and pattern recognition
- Export functionality for further analysis

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `src/`
  - `processors/`: Text processing and AI analysis modules
  - `utils/`: Utility functions and helpers
  - `visualization/`: Data visualization components
  - `config.py`: Configuration settings
  - `models.py`: Data models and structures

## Usage

1. Input interview data through text input or file upload
2. Process interviews to extract key statements
3. Analyze results and generate insights
4. Export findings in various formats

## Privacy & Security

- All data is processed locally
- Optional data encryption
- Compliant with privacy regulations
- Secure data storage practices 