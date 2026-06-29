# Prompt Builder (Streamlit)

A local web app to convert your input/context into a high-quality, structured prompt for:
- Create Dashboard
- Analyze Code
- Rewrite Code

## Features
- **File Upload**: Browse and upload multiple files (code, text, JSON, SQL, CSV, etc.)
- **Token-Efficient Prompts**: Optimized templates to minimize token usage while maintaining clarity
- **Multiple Task Types**: Dashboard design, code analysis, code rewriting
- **Flexible Output**: Plain text or structured JSON format with predefined schemas
- **Customizable**: Adjust tone, add requirements, enable clarifying questions
- **Token Estimation**: Real-time token count estimation for cost optimization
- **Session Persistence**: Generated prompts persist across interactions

## Quick start

1. (Optional) Create and activate a virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
```
2. Install dependencies:
   
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   
   ```bash
   kill $(lsof -t -i:8501) || true && python3 -m streamlit run app.py --server.port 8501
   ```

4. Open the local URL shown in the terminal (typically http://localhost:8501).

## Usage
1. **Upload files** or paste context directly in the input area
2. Configure settings in the sidebar (task type, tone, format, etc.)
3. Enable "Token-efficient prompts" for optimized token usage
4. Click "Generate prompt" to create your structured prompt
5. Download the result as a .txt file

## Task Types

### Create Dashboard
Design decision-focused dashboards with KPIs, visualizations, layouts, and implementation plans.

### Analyze Code
Comprehensive code review including bug detection, security issues, performance analysis, and refactoring recommendations.

### Rewrite Code
Code improvement focused on readability, security, and performance while preserving API semantics.

## JSON Output Schemas

Each task type has a predefined JSON schema for structured output:
- **Create Dashboard**: personas, decisions, KPIs, visuals, layout, sources, implementation notes
- **Analyze Code**: summary, issues (bug/security/performance/style), complexity metrics, tests, refactors, risks
- **Rewrite Code**: code blocks, changes, compatibility notes, tests, migration guide

## Notes
- No external API keys required - runs entirely locally
- Supports multiple file uploads for batch processing (.py, .js, .ts, .json, .md, .sql, .csv, .txt)
- Token-efficient mode reduces prompt length while maintaining clarity
- Real-time token estimation helps optimize costs
- Generated prompts can be downloaded as .txt files
