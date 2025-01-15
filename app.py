import streamlit as st
import pandas as pd
from datetime import datetime
from src.processors.ai_processor import process_interview_with_ai
from src.utils.file_handlers import read_file_content
from src.utils.storage import (
    save_interview,
    load_interviews,
    delete_interview,
    mark_for_analysis,
    save_analysis_version,
    load_analysis_versions,
    get_latest_analysis_version
)
from src.models import Interview, Statement, StatementType

st.set_page_config(
    page_title="AI Interview Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'interviews' not in st.session_state:
    st.session_state.interviews = load_interviews()

def process_interview_data(text: str, interviewee: str) -> Interview:
    """Process interview data and return an Interview object."""
    try:
        print(f"\n=== Processing interview for: {interviewee} ===")
        
        # Process interview with AI
        interview = process_interview_with_ai(text, interviewee)
        
        # Generate filename with microseconds for uniqueness
        filename = f"{interviewee.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        print(f"Generated filename: {filename}")
        
        # Initialize metadata if not present
        if not hasattr(interview, 'metadata') or interview.metadata is None:
            interview.metadata = {}
        
        # Add filename to metadata
        interview.metadata['filename'] = filename
        interview.metadata['ready_for_analysis'] = False
        interview.metadata['created_at'] = datetime.now().isoformat()
        
        print(f"Interview metadata: {interview.metadata}")
        print(f"Number of statements: {len(interview.statements)}")
        
        # Save interview
        if save_interview(interview):
            print("✓ Interview saved successfully")
            st.session_state.interviews = load_interviews()  # Reload interviews
        else:
            print("❌ Failed to save interview")
            raise Exception("Failed to save interview")
            
        return interview
        
    except Exception as e:
        print(f"❌ Error in process_interview_data: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

def display_statements_table(interview: Interview, index: int = 0, context: str = "default"):
    """Display statements in a searchable table."""
    if not interview.statements:
        st.warning("Geen statements gevonden in de tekst.")
    
    # Create unique key base with index and context to prevent duplicates
    key_base = f"{interview.metadata['filename']}_{context}_{index}"
    
    # Create DataFrame
    data = [{
        'Type': s.type.value,
        'Statement': s.text,
        'Confidence': f"{s.confidence:.2f}"
    } for s in interview.statements]
    
    df = pd.DataFrame(data)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Add search functionality with unique key
        search = st.text_input("🔍 Zoek in statements", "", key=f"search_{key_base}")
        if search:
            df = df[df['Statement'].str.contains(search, case=False)]
    
    with col2:
        # Add analysis toggle with unique key
        ready_for_analysis = interview.metadata.get('ready_for_analysis', False)
        toggle_key = f"toggle_{key_base}"
        
        # Use the actual file state instead of session state
        if st.toggle("Klaar voor analyse", value=ready_for_analysis, key=toggle_key, help="Markeer dit interview als klaar voor analyse"):
            if not ready_for_analysis:  # Only update if state changed from False to True
                if mark_for_analysis(interview.metadata['filename'], True):
                    st.success("Interview gemarkeerd voor analyse")
                    st.session_state.interviews = load_interviews()
                    st.rerun()
        else:
            if ready_for_analysis:  # Only update if state changed from True to False
                if mark_for_analysis(interview.metadata['filename'], False):
                    st.info("Interview niet meer gemarkeerd voor analyse")
                    st.session_state.interviews = load_interviews()
                    st.rerun()
    
    with col3:
        # Initialize delete state for this interview if not exists
        delete_key = f"delete_{key_base}"
        
        if delete_key not in st.session_state:
            st.session_state[delete_key] = False
        
        # Add delete button with confirmation
        if not st.session_state[delete_key]:
            if st.button("🗑️ Verwijder", key=f"delete_btn_{key_base}", type="secondary"):
                print(f"\n=== Delete button clicked for: {interview.metadata['filename']} ===")
                st.session_state[delete_key] = True
                st.rerun()
        else:
            # Show confirmation dialog
            st.warning("Weet je zeker dat je dit interview wilt verwijderen?")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✓ Ja", key=f"confirm_{key_base}", type="primary"):
                    try:
                        print(f"\n=== Delete confirmed for: {interview.metadata['filename']} ===")
                        filename = interview.metadata.get('filename')
                        if not filename:
                            st.error("Geen bestandsnaam gevonden voor dit interview")
                            print("❌ No filename found in metadata")
                        else:
                            print(f"Attempting to delete file: {filename}")
                            if delete_interview(filename):
                                print("✓ File deleted successfully")
                                # Remove from session state immediately
                                old_len = len(st.session_state.interviews)
                                st.session_state.interviews = [i for i in st.session_state.interviews if i.metadata.get('filename') != filename]
                                new_len = len(st.session_state.interviews)
                                print(f"Interviews in session state: {old_len} -> {new_len}")
                                
                                # Clear delete state
                                del st.session_state[delete_key]
                                st.success("Interview verwijderd")
                                st.rerun()
                            else:
                                st.error("Fout bij verwijderen interview")
                                print("❌ delete_interview returned False")
                    except Exception as e:
                        print(f"❌ Error in delete confirmation: {str(e)}")
                        import traceback
                        print(f"Traceback: {traceback.format_exc()}")
                        st.error(f"Fout bij verwijderen: {str(e)}")
            with col2:
                if st.button("✗ Nee", key=f"cancel_{key_base}"):
                    print(f"\n=== Delete cancelled for: {interview.metadata['filename']} ===")
                    del st.session_state[delete_key]
                    st.rerun()
    
    # Display editable table with unique key
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Type": st.column_config.SelectboxColumn(
                "Type",
                width="medium",
                options=[t.value for t in StatementType],
                required=True
            ),
            "Statement": st.column_config.TextColumn(
                "Statement",
                width="large",
                required=True
            ),
            "Confidence": st.column_config.NumberColumn(
                "Confidence",
                width="small",
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
                required=True,
                default=1.0
            ),
        },
        key=f"editor_{key_base}"
    )
    
    # Check if table was edited
    if not df.equals(edited_df):
        # Update statements
        new_statements = []
        for _, row in edited_df.iterrows():
            statement = Statement(
                text=row['Statement'],
                type=StatementType(row['Type']),
                source_text="",  # Empty for manually added/edited statements
                confidence=float(row['Confidence']),
                metadata={'edited': True}
            )
            new_statements.append(statement)
        
        # Update interview
        interview.statements = new_statements
        interview.metadata['last_edited'] = datetime.now().isoformat()
        
        # Save changes
        if save_interview(interview):
            st.success("Wijzigingen opgeslagen")
            st.session_state.interviews = load_interviews()
        else:
            st.error("Fout bij opslaan van wijzigingen")
    
    # Add download button with unique key
    if st.button("Download als CSV", key=f"download_{key_base}"):
        csv = edited_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"interview_statements_{interview.interviewee}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"download_button_{key_base}"
        )

def main():
    st.title("🎯 AI Interview Analyzer")
    
    tab1, tab2 = st.tabs(["Interview Verwerking", "Analyse & Conclusies"])
    
    with tab1:
        st.header("Interview Verwerking")
        
        # Input section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            interviewee = st.text_input("Naam geïnterviewde", key="input_interviewee")
            
            # Text input option
            text_input = st.text_area(
                "Interview tekst",
                height=200,
                help="Plak hier de interview tekst of upload een bestand",
                key="input_text"
            )
            
            # File upload option
            uploaded_file = st.file_uploader(
                "Of upload een bestand",
                type=['txt', 'doc', 'docx', 'pdf'],
                help="Ondersteunde formaten: TXT, DOC, DOCX, PDF",
                key="file_upload"
            )
        
        with col2:
            st.markdown("### Tips")
            st.markdown("""
            - Zorg dat de tekst duidelijk is opgemaakt
            - Verwijder onnodige headers/footers
            - Splits lange interviews in delen
            - Check de resultaten na verwerking
            """)
        
        # Process button
        if st.button("Verwerk Interview", type="primary"):
            if not interviewee:
                st.error("Vul eerst de naam van de geïnterviewde in.")
                return
            
            if not text_input and not uploaded_file:
                st.error("Voeg interview tekst toe of upload een bestand.")
                return
            
            with st.spinner("Interview verwerken..."):
                try:
                    # Get text content
                    if uploaded_file:
                        text = read_file_content(uploaded_file)
                    else:
                        text = text_input
                    
                    # Process interview
                    interview = process_interview_data(text, interviewee)
                    
                    st.success("Interview succesvol verwerkt!")
                    
                    # Display results
                    st.subheader("Resultaten")
                    display_statements_table(interview, context="results")
                    
                except Exception as e:
                    st.error(f"Error bij verwerken: {str(e)}")
        
        # Show existing interviews
        if st.session_state.interviews:
            st.subheader("Verwerkte Interviews")
            for idx, interview in enumerate(st.session_state.interviews):
                ready_status = "✅" if interview.metadata.get('ready_for_analysis', False) else "⏳"
                with st.expander(f"Interview: {interview.interviewee} {ready_status}"):
                    display_statements_table(interview, idx, context="list")
    
    with tab2:
        st.header("Analyse & Conclusies")
        
        # Filter interviews that are ready for analysis
        ready_interviews = [i for i in st.session_state.interviews if i.metadata.get('ready_for_analysis', False)]
        
        if not ready_interviews:
            st.info("Geen interviews gemarkeerd voor analyse. Markeer eerst interviews als 'Klaar voor analyse' in de Interview Verwerking tab.")
        else:
            st.success(f"{len(ready_interviews)} interview(s) klaar voor analyse")
            
            # Create tabs for different analysis views
            analysis_tab1, analysis_tab2 = st.tabs(["Onderzoeksvragen", "Statements Doorzoeken"])
            
            with analysis_tab1:
                st.subheader("Onderzoeksvragen Analyseren")
                
                # Get latest analysis version if it exists
                latest_version = get_latest_analysis_version()
                
                # Research questions input
                if 'research_questions' not in st.session_state:
                    st.session_state.research_questions = [""]
                
                # Add/remove question buttons
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write("Voer je onderzoeksvragen in:")
                with col2:
                    if st.button("➕ Vraag Toevoegen"):
                        st.session_state.research_questions.append("")
                        st.rerun()
                
                # Question inputs
                questions_to_remove = []
                for i, question in enumerate(st.session_state.research_questions):
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.session_state.research_questions[i] = st.text_input(
                            f"Vraag {i+1}",
                            value=question,
                            key=f"question_{i}",
                            placeholder="Typ hier je onderzoeksvraag..."
                        )
                    with col2:
                        if len(st.session_state.research_questions) > 1 and st.button("❌", key=f"remove_{i}"):
                            questions_to_remove.append(i)
                
                # Remove marked questions
                for i in reversed(questions_to_remove):
                    st.session_state.research_questions.pop(i)
                    st.rerun()
                
                # Initialize analysis state
                if 'current_analysis' not in st.session_state and latest_version:
                    st.session_state.current_analysis = latest_version
                
                # Analyze button
                if st.button("🔍 Analyseer", type="primary") or (not latest_version and not st.session_state.get('current_analysis')):
                    # Validate questions
                    valid_questions = [q for q in st.session_state.research_questions if q.strip()]
                    if not valid_questions:
                        st.error("Voer ten minste één onderzoeksvraag in.")
                    else:
                        with st.spinner("Interviews analyseren..."):
                            try:
                                from src.processors.analysis_processor import analyze_interviews
                                analysis_result = analyze_interviews(ready_interviews, valid_questions)
                                
                                if analysis_result:
                                    st.success(f"Analyse voltooid! {analysis_result['statements_analyzed']} statements geanalyseerd van {analysis_result['interviews_analyzed']} interviews.")
                                    
                                    # Create formatted markdown with metadata
                                    markdown_text = f"""# Interview Analyse Rapport
Datum: {datetime.now().strftime('%d-%m-%Y %H:%M')}
Aantal interviews: {analysis_result['interviews_analyzed']}
Aantal statements: {analysis_result['statements_analyzed']}

## Onderzoeksvragen
{chr(10).join(f"- {q}" for q in analysis_result['questions'])}

## Analyse
{analysis_result['raw_response']}
"""
                                    
                                    # Save initial version
                                    version_metadata = {
                                        'version_type': 'initial',
                                        'interviews_analyzed': analysis_result['interviews_analyzed'],
                                        'statements_analyzed': analysis_result['statements_analyzed']
                                    }
                                    save_analysis_version(markdown_text, valid_questions, version_metadata)
                                    
                                    # Update current analysis in session state
                                    st.session_state.current_analysis = {
                                        'text': markdown_text,
                                        'questions': valid_questions,
                                        'metadata': version_metadata,
                                        'timestamp': datetime.now().isoformat(),
                                        'version_type': 'initial'
                                    }
                                else:
                                    st.error("Er is een fout opgetreden bij de analyse.")
                            except Exception as e:
                                st.error(f"Error tijdens analyse: {str(e)}")
                
                # Only show analysis tabs if we have an analysis
                if st.session_state.get('current_analysis'):
                    # Create tabs for different views
                    view_tab, raw_tab, chat_tab, versions_tab = st.tabs([
                        "📊 Opgemaakte Weergave",
                        "📝 Markdown Bewerken",
                        "💬 Chat met AI",
                        "📚 Versies"
                    ])
                    
                    with view_tab:
                        st.markdown(st.session_state.current_analysis['text'])
                    
                    with raw_tab:
                        # Display editable markdown block
                        edited_markdown = st.text_area(
                            "Markdown Bewerken",
                            value=st.session_state.current_analysis['text'],
                            height=400,
                            key="markdown_edit"
                        )
                        
                        # Save button for manual edits
                        if st.button("💾 Wijzigingen Opslaan"):
                            version_metadata = {
                                'version_type': 'manual',
                                'interviews_analyzed': st.session_state.current_analysis['metadata']['interviews_analyzed'],
                                'statements_analyzed': st.session_state.current_analysis['metadata']['statements_analyzed']
                            }
                            if save_analysis_version(edited_markdown, st.session_state.current_analysis['questions'], version_metadata):
                                st.success("Wijzigingen opgeslagen als nieuwe versie")
                                # Update current analysis
                                st.session_state.current_analysis['text'] = edited_markdown
                                st.session_state.current_analysis['metadata'] = version_metadata
                                st.session_state.current_analysis['timestamp'] = datetime.now().isoformat()
                                st.session_state.current_analysis['version_type'] = 'manual'
                                st.rerun()
                    
                    with chat_tab:
                        st.markdown("### Chat met AI over de Analyse")
                        st.markdown("""
                        Hier kun je vragen stellen over de analyse of verzoeken doen voor herformatteringen.
                        De AI zal alleen conclusies trekken op basis van de statements uit de interviews.
                        """)
                        
                        # Initialize chat history
                        if 'chat_history' not in st.session_state:
                            st.session_state.chat_history = []
                        
                        # Display chat history
                        for msg in st.session_state.chat_history:
                            with st.chat_message(msg["role"]):
                                st.markdown(msg["content"])
                        
                        # Chat input
                        if prompt := st.chat_input("Typ je vraag of verzoek..."):
                            # Add user message to history
                            st.session_state.chat_history.append({"role": "user", "content": prompt})
                            
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            
                            with st.chat_message("assistant"):
                                with st.spinner("AI denkt na..."):
                                    from src.processors.analysis_processor import chat_with_analysis
                                    response = chat_with_analysis(
                                        prompt,
                                        ready_interviews,
                                        st.session_state.current_analysis['questions'],
                                        st.session_state.chat_history
                                    )
                                    
                                    st.markdown(response['message'])
                                    
                                    # Update current analysis if we got a new version
                                    if response.get('new_analysis'):
                                        version_metadata = {
                                            'version_type': 'ai_chat',
                                            'prompt': prompt,
                                            'interviews_analyzed': st.session_state.current_analysis['metadata']['interviews_analyzed'],
                                            'statements_analyzed': st.session_state.current_analysis['metadata']['statements_analyzed']
                                        }
                                        save_analysis_version(
                                            response['new_analysis'],
                                            st.session_state.current_analysis['questions'],
                                            version_metadata
                                        )
                                        # Update current analysis
                                        st.session_state.current_analysis['text'] = response['new_analysis']
                                        st.session_state.current_analysis['metadata'] = version_metadata
                                        st.session_state.current_analysis['timestamp'] = datetime.now().isoformat()
                                        st.session_state.current_analysis['version_type'] = 'ai_chat'
                            
                            # Add assistant response to history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response['message']
                            })
                    
                    with versions_tab:
                        st.markdown("### Analyse Versies")
                        versions = load_analysis_versions()
                        
                        for version in versions:
                            with st.expander(f"Versie van {version['timestamp']} ({version['version_type']})"):
                                st.markdown(version['text'])
                                
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    # Export to Word
                                    from src.utils.export import markdown_to_docx
                                    docx_file = markdown_to_docx(version['text'])
                                    
                                    st.download_button(
                                        label="📎 Download als Word",
                                        data=docx_file,
                                        file_name=f"interview_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        key=f"word_download_{version['filename']}"
                                    )
                                    
                                    # Add button to make this version current
                                    if st.button("Maak Actief", key=f"activate_{version['filename']}"):
                                        st.session_state.current_analysis = version
                                        st.rerun()
            
            with analysis_tab2:
                st.subheader("Statements Doorzoeken")
                
                # Search functionality
                search_query = st.text_input("🔍 Zoek in alle statements", placeholder="Typ om te zoeken...")
                
                if search_query:
                    from src.processors.analysis_processor import search_analysis_statements
                    matching_statements = search_analysis_statements(ready_interviews, search_query)
                    
                    if matching_statements:
                        # Create DataFrame
                        data = [{
                            'Interview': s.metadata.get('interview_name', 'Onbekend'),
                            'Type': s.type.value,
                            'Statement': s.text,
                            'Confidence': f"{s.confidence:.2f}"
                        } for s in matching_statements]
                        
                        df = pd.DataFrame(data)
                        
                        # Display results
                        st.dataframe(
                            df,
                            use_container_width=True,
                            column_config={
                                "Interview": st.column_config.TextColumn("Interview", width="medium"),
                                "Type": st.column_config.TextColumn("Type", width="small"),
                                "Statement": st.column_config.TextColumn("Statement", width="large"),
                                "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                            }
                        )
                        
                        # Add export button
                        if st.button("Download Zoekresultaten"):
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info("Geen statements gevonden die aan je zoekcriteria voldoen.")

if __name__ == "__main__":
    main() 