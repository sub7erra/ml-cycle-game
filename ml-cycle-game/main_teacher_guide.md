This file is for the overall platform, not a specific lesson.

# Main Teacher's Guide: Escape Room Platform

## 1. How the App Works & Deployment

This application is a modular platform designed to host multiple data science "escape room" scenarios. It is designed for deployment on free cloud services, making it easily accessible for students.

### Local Development Setup:
1.  **Ensure Python is installed.** (Version 3.10+ recommended).
2.  **Install dependencies:** In your terminal, navigate to the project folder and run `pip install -r requirements.txt`.
3.  **Create `.env` file:** Create this file in the project root. This is where you'll store your API key for testing on your own machine.
4.  **Get API Key:** Obtain an API key from Google AI Studio and place it in the `.env` file: `GOOGLE_API_KEY="your_key_here"`.
5.  **Select model (optional):** You can override the default model via `GEMINI_MODEL_NAME`. Default is `gemini-2.5-flash-lite`.
6.  **Run Locally:** `streamlit run app.py`. Your browser should open with the running application.

> Env vars supported:
> - `GOOGLE_API_KEY`: required for LLM mode
> - `GEMINI_MODEL_NAME`: e.g., `gemini-2.5-flash-lite` (default)
> - `LLM_TIMEOUT_SECS`: request timeout in seconds (default 15)

### Deployment for the Class (Choose one option)
**Before you deploy, create a GitHub repository and upload your project files. The `.gitignore` file is crucial as it will prevent your secret `.env` file from being uploaded.**

#### Option A: Deploying to Streamlit Community Cloud
1.  **Sign up** for a free account at `share.streamlit.io` using your GitHub account.
2.  **Deploy the app:**
    - Click "New app" and select your GitHub repository.
    - Go to "Advanced settings..."
    - In the "Secrets" section, add your API key. Secrets are Streamlit's secure way of storing sensitive information.
      ```toml
      GOOGLE_API_KEY = "your_actual_google_api_key_xxxxxxxxxx"
      GEMINI_MODEL_NAME = "gemini-2.5-flash-lite"
      ```
    - Click "Save" and then "Deploy".
3.  **Share the Link:** You will get a public URL (e.g., `your-app-name.streamlit.app`) to share with students.

#### Option B: Deploying to Hugging Face Spaces
1.  **Sign up** for a free account at `huggingface.co`.
2.  **Create a new Space:**
    - Click your profile icon, then "New Space".
    - Give your Space a name, select "Streamlit" as the Space SDK, and choose the free hardware tier.
    - Link your existing GitHub repository.
3.  **Add your Secret Key:**
    - After the Space is created, go to the "Settings" tab.
    - Find the "Repository secrets" section and click "New secret".
    - For **Name**, enter `GOOGLE_API_KEY`.
    - (Optional) Add `GEMINI_MODEL_NAME`.
4.  **Share the Link:** You will get a public URL (e.g., `your-name-your-space.hf.space`) to share.

*(Note: The `app.py` code works with both platforms without changes.)*

## 2. Adding New Scenarios
This app is designed to be extensible via a "convention over configuration" approach.
1.  Create a new sub-folder inside the `scenarios/` directory (e.g., `scenarios/customer_churn_prediction/`).
2.  Inside this new folder, replicate the required file structure: a `lore.md`, a `scenario_teacher_guide.md`, and a `rooms/` directory containing the markdown files for your new scenario.
3.  Provide a `data/fields.csv` with field metadata (name, description, type, category, is_target). The app uses this as the canonical catalog.
4.  For each room, provide two files: a student-facing `.md` and a `_system.md` containing the LLM/system instructions. The app reads prompts from these files.
5.  The main `app.py` will automatically detect the new folder and add it to the scenario selection screen. No core code changes are needed.

## 3. LLM Behavior & Progression
- Personas are instructed to be self-contained, avoid revealing answer keys, and respond politely with process guidance.
- Rooms unlock based on clear criteria:
  - Room 1 (PM): JSON `{ unlocked: true }` if plan hits metric/task/baseline criteria.
  - Room 2 (Data Steward): Unlocks after ≥10 confirmed fields. Steward replies in JSON and the UI shows only `message`.
  - Room 3 (PM): JSON `{ unlocked: true }` if method + numeric evidence + interpretation are present.
  - Room 4 (Field Expert): Accumulate ≥30 points via JSON scoring.
  - Room 5: Final selector; checks that `id` and `date` are deselected.
- After a room unlocks, chat input for that room is disabled (history remains visible) and navigation buttons are enabled.

## 4. Troubleshooting
- **Quota/429 errors:** Enable billing for your Gemini API project and/or select a cost-efficient model like `gemini-2.5-flash-lite`.
- **Freezes:** The app uses a safe timeout for LLM calls (`LLM_TIMEOUT_SECS`) and runs requests on a daemon thread to avoid shutdown hangs.
- **JSON shows in chat:** The UI extracts and displays only the `message` field from persona JSON.
- **Dataset download locked:** Ensure students discovered ≥10 fields in Room 2.

## 5. Instructor Tools
- `scenarios/<scenario>/cheats.md` contains ready-to-paste messages to quickly unlock rooms for demos.

