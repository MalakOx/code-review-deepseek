import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(
    page_title="Code Review Assistant",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .review-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🔍 Code Review Assistant</h1><p>Powered by DeepSeek-Coder via Ollama</p></div>', unsafe_allow_html=True)

# Sidebar for instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    1. **Paste your code** in the text area
    2. **Keep it under 5000 characters** for best performance
    3. **Click 'Get Review'** to analyze
    4. **Wait patiently** - analysis can take 1-2 minutes
    5. **Review the feedback** and suggestions
    
    **Performance Tips:**
    - Smaller code blocks = faster processing
    - Break large files into logical sections
    - Remove comments/whitespace if hitting limits
    
    **Supported Languages:**
    - Python, JavaScript, Java, C/C++, Go, Rust, TypeScript, and more
    
    **Troubleshooting Timeouts:**
    - Reduce code size to under 2000 characters
    - Check if DeepSeek-Coder model is running
    - Restart Ollama service if needed
    """)
    
    st.header("⚙️ System Status")
    if st.button("Check Backend Status"):
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "healthy":
                    st.success("✅ Backend is running")
                    st.success("✅ Ollama is connected")
                    
                    # Additional model check
                    st.info("💡 If you're experiencing timeouts, try: `ollama ps` to check model status")
                else:
                    st.error("❌ Ollama is disconnected")
                    st.markdown("**Try:** `ollama serve` to start Ollama")
            else:
                st.error("❌ Backend is not responding")
        except:
            st.error("❌ Cannot connect to backend")
            st.markdown("**Try:** Start backend with `uvicorn backend.main:app --reload`")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Code Input")
    
    # Language selection
    language = st.selectbox(
        "Select Programming Language:",
        ["python", "javascript", "java", "cpp", "go", "rust", "typescript", "html", "css", "sql", "other"]
    )
    
    # Code input area
    code_input = st.text_area(
        "Paste your code here:",
        height=400,
        placeholder="Enter your code here for review...",
        help="Paste the code you want to review. For best performance, keep code under 5000 characters.",
        max_chars=5000  # Add character limit
    )
    
    # Show character count
    if code_input:
        char_count = len(code_input)
        if char_count > 4000:
            st.warning(f"⚠️ Code length: {char_count}/5000 characters. Large code blocks may take longer to process.")
        else:
            st.info(f"Code length: {char_count} characters")
    
    # Review button with better handling
    if st.button("🔍 Get Code Review", type="primary", use_container_width=True):
        if not code_input.strip():
            st.error("Please enter some code to review!")
        else:
            with st.spinner("Analyzing your code... This may take 1-2 minutes for large code blocks."):
                try:
                    # Show progress bar
                    progress_bar = st.progress(0)
                    progress_bar.progress(25)
                    
                    response = requests.post(
                        "http://localhost:8000/review/",
                        data={"code": code_input},
                        timeout=150  # Increased timeout to 2.5 minutes
                    )
                    
                    progress_bar.progress(100)
                    
                    if response.status_code == 200:
                        result = response.json()
                        review = result.get("review", "No feedback returned.")
                        code_length = result.get("code_length", len(code_input))
                        
                        st.session_state.review = review
                        st.session_state.reviewed_code = code_input
                        st.session_state.code_stats = {"length": code_length}
                        
                        progress_bar.empty()
                        st.success("✅ Code review completed!")
                        
                    elif response.status_code == 504:
                        progress_bar.empty()
                        st.error("⏱️ The review timed out. Try these solutions:")
                        st.markdown("""
                        **Troubleshooting Steps:**
                        1. **Reduce code size**: Break your code into smaller chunks
                        2. **Check Ollama**: Run `ollama ps` to see if DeepSeek-Coder is loaded
                        3. **Restart model**: Run `ollama stop deepseek-coder` then try again
                        4. **System resources**: Ensure you have enough RAM (4GB+ recommended)
                        """)
                    else:
                        progress_bar.empty()
                        error_detail = response.json().get("detail", f"HTTP {response.status_code}")
                        st.error(f"❌ Error: {error_detail}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timed out. Try these solutions:")
                    st.markdown("""
                    **Quick Fixes:**
                    - **Reduce code size**: Paste smaller code blocks (under 2000 characters)
                    - **Check model status**: Ensure DeepSeek-Coder is running properly
                    - **Restart Ollama**: Sometimes the model needs to be reloaded
                    
                    **Commands to try:**
                    ```bash
                    ollama ps                    # Check running models
                    ollama stop deepseek-coder   # Stop the model
                    ollama run deepseek-coder    # Restart the model
                    ```
                    """)
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to the backend. Make sure the FastAPI server is running on port 8000.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

with col2:
    st.header("📊 Code Review Results")
    
    if hasattr(st.session_state, 'review') and st.session_state.review:
        st.markdown('<div class="review-container">', unsafe_allow_html=True)
        st.markdown(f"**AI Code Review ({st.session_state.get('review_time', '')}):**")
        st.markdown(st.session_state.review)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display the original code with syntax highlighting
        st.markdown("**Original Code:**")
        st.code(
            body=st.session_state.reviewed_code,
            language=st.session_state.review_language
        )
        
        # Option to download review - using string concatenation to avoid triple-quote issues
        if st.button("📥 Download Review"):
            review_content = (
                f"# Code Review Report ({st.session_state.review_time})\n\n"
                f"## Original Code:\n"
                f"```{st.session_state.review_language}\n"
                f"{st.session_state.reviewed_code}\n"
                f"```\n\n"
                f"## Review:\n"
                f"{st.session_state.review}"
            )
            
            st.download_button(
                label="📥 Download Review",
                data=review_content,
                file_name=f"code_review_{st.session_state.review_time.replace(':', '-')}.md",
                mime="text/markdown",
                key="download_review"  # Added key to prevent duplicate widget ID
            )