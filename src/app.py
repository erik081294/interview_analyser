def display_chat():
    """Display the chat interface with improved styling."""
    st.markdown("""
        <style>
        /* Chat container */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Message container */
        .stTextInput > div {
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* User message */
        .user-message {
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
            margin: 10px 0;
            gap: 10px;
        }
        
        .user-message-content {
            background-color: #007AFF;
            color: white;
            padding: 10px 15px;
            border-radius: 15px 15px 0 15px;
            max-width: 70%;
        }
        
        /* Assistant message */
        .assistant-message {
            display: flex;
            justify-content: flex-start;
            align-items: flex-start;
            margin: 10px 0;
            gap: 10px;
        }
        
        .assistant-message-content {
            background-color: #E9ECEF;
            color: black;
            padding: 10px 15px;
            border-radius: 15px 15px 15px 0;
            max-width: 70%;
        }
        
        /* Message icons */
        .message-icon {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .user-icon {
            background-color: #007AFF;
            color: white;
        }
        
        .assistant-icon {
            background-color: #E9ECEF;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Display welcome message if no history
    if not st.session_state.chat_history:
        st.markdown("""
            <div class="chat-container">
                <div class="assistant-message">
                    <div class="message-icon assistant-icon">🤖</div>
                    <div class="assistant-message-content">
                        Hier kun je vragen stellen over de analyse of verzoeken doen voor herformattering. 
                        De AI zal alleen conclusies trekken op basis van de statements uit de interviews.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
                <div class="chat-container">
                    <div class="user-message">
                        <div class="user-message-content">{msg["content"]}</div>
                        <div class="message-icon user-icon">👤</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-container">
                    <div class="assistant-message">
                        <div class="message-icon assistant-icon">🤖</div>
                        <div class="assistant-message-content">{msg["content"]}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Chat input
    user_input = st.text_input("Type je vraag of verzoek...", key="chat_input")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Display user message
        st.markdown(f"""
            <div class="chat-container">
                <div class="user-message">
                    <div class="user-message-content">{user_input}</div>
                    <div class="message-icon user-icon">👤</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Process and display AI response
        with st.spinner("AI denkt na..."):
            response = process_chat_message(user_input)
            
            st.markdown(f"""
                <div class="chat-container">
                    <div class="assistant-message">
                        <div class="message-icon assistant-icon">🤖</div>
                        <div class="assistant-message-content">{response}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Rerun to update the display
            st.rerun()

def show_analysis_tab():
    st.header("Analyse & Conclusies")
    
    # Filter interviews that are ready for analysis
    ready_interviews = [i for i in st.session_state.interviews if i.metadata.get('ready_for_analysis', False)]
    
    if not ready_interviews:
        st.info("Geen interviews gemarkeerd voor analyse. Markeer eerst interviews als 'Klaar voor analyse' in de Interview Verwerking tab.")
        return
    
    st.success(f"{len(ready_interviews)} interview(s) klaar voor analyse")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Chat met AI", "Markdown", "Zoeken"])
    
    with tab1:
        display_chat()
    
    with tab2:
        if 'current_analysis' in st.session_state:
            st.markdown(st.session_state.current_analysis['text'])
            
            # Add download button
            if st.button("Download als Word"):
                from src.utils.export import markdown_to_docx
                docx_file = markdown_to_docx(st.session_state.current_analysis['text'])
                
                st.download_button(
                    label="📎 Download Word Document",
                    data=docx_file,
                    file_name=f"interview_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.info("Nog geen analyse beschikbaar. Start een chat om een analyse te maken.")
    
    with tab3:
        st.subheader("Statements Doorzoeken")
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

def main():
    st.title("🎯 AI Interview Analyzer")
    
    # Initialize session state
    if 'interviews' not in st.session_state:
        st.session_state.interviews = load_interviews()

    # Set page config
    st.set_page_config(
        page_title="AI Interview Analyzer",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add custom CSS for chat styling
    st.markdown("""
        <style>
        /* Chat container */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Message container */
        .stTextInput > div {
            max-width: 800px;
            margin: 0 auto;
        }
        
        /* User message */
        .user-message {
            display: flex;
            justify-content: flex-end;
            align-items: flex-start;
            margin: 10px 0;
            gap: 10px;
        }
        
        .user-message-content {
            background-color: #007AFF;
            color: white;
            padding: 10px 15px;
            border-radius: 15px 15px 0 15px;
            max-width: 70%;
        }
        
        /* Assistant message */
        .assistant-message {
            display: flex;
            justify-content: flex-start;
            align-items: flex-start;
            margin: 10px 0;
            gap: 10px;
        }
        
        .assistant-message-content {
            background-color: #E9ECEF;
            color: black;
            padding: 10px 15px;
            border-radius: 15px 15px 15px 0;
            max-width: 70%;
        }
        
        /* Message icons */
        .message-icon {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .user-icon {
            background-color: #007AFF;
            color: white;
        }
        
        .assistant-icon {
            background-color: #E9ECEF;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Interview Verwerking", "Analyse & Conclusies"])
    
    with tab1:
        # ... existing interview processing code ...
        pass
    
    with tab2:
        show_analysis_tab()

if __name__ == "__main__":
    main() 