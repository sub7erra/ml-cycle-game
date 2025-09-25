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

This app uses a modular architecture that makes it easy to add new scenarios. Each scenario is self-contained with its own configuration and logic.

### Architecture Overview

```
ml-cycle-game/
├── app.py                           # Main framework (UI + routing)
├── tools/                           # Shared utilities package
│   ├── __init__.py                  # Exports utilities
│   └── core.py                      # Implementation
└── scenarios/                       # Scenarios package
    ├── __init__.py                  # Package marker
    ├── base.py                      # BaseScenario class
    ├── download_config.py           # Download configuration system
    └── <scenario_name>/             # Individual scenario
        ├── __init__.py              # Package marker
        ├── scenario.py              # Scenario implementation
        ├── download_config.py       # Scenario-specific downloads
        ├── lore.md                  # Scenario metadata & personas
        ├── teacher_guide.md         # Teaching guide
        ├── cheats.md                # Demo shortcuts
        ├── data/                    # Dataset files
        │   ├── data.csv             # Main dataset
        │   └── fields.csv           # Field metadata
        └── rooms/                   # Room content
            ├── room_0_introduction.md
            ├── room_1_briefing.md
            ├── room_1_briefing_system.md
            └── ...                  # Other rooms
```

### Step-by-Step Guide to Add a New Scenario

#### 1. Create Scenario Directory Structure
```bash
mkdir scenarios/your_scenario_name
mkdir scenarios/your_scenario_name/data
mkdir scenarios/your_scenario_name/rooms
touch scenarios/your_scenario_name/__init__.py
```

#### 2. Create Download Configuration
Create `scenarios/your_scenario_name/download_config.py`:
```python
from typing import Dict
from ..download_config import (
    BaseDownloadConfig,
    RoomDownloads,
    DownloadFile,
    FileType,
    DownloadGroup,
)

class YourScenarioDownloadConfig(BaseDownloadConfig):
    """Download configuration for your scenario."""
    
    def _get_room_configs(self) -> Dict[int, RoomDownloads]:
        """Get the room download configurations."""
        return {
            3: RoomDownloads(  # Example: Room 3 has downloads
                room_number=3,
                room_name="EDA Report",
                files=[
                    DownloadFile(
                        filename="data.csv",
                        file_type=FileType.DATASET,
                        group=DownloadGroup.DATA,
                        description="Main dataset for your scenario",
                    ),
                    # Add more files as needed
                ]
            )
        }
```

#### 3. Create Scenario Implementation
Create `scenarios/your_scenario_name/scenario.py`:
```python
from ..base import BaseScenario
from .download_config import YourScenarioDownloadConfig
from tools import (
    read_markdown_file,
    json_message_display_transform,
    extract_first_json_object,
    extract_known_fields_from_text,
    do_rerun,
)
from app import ui_chat_area

class YourScenarioScenario(BaseScenario):
    """Scenario implementation for your scenario."""
    
    def _get_download_config(self):
        """Get the download configuration for this scenario."""
        return YourScenarioDownloadConfig(self.scenario_dir)
    
    def _is_room_downloads_unlocked(self, room_number: int) -> bool:
        """Check if downloads for a specific room are unlocked."""
        if room_number == 3:  # Example unlock condition
            return len(st.session_state.get("discovered_fields_info", {})) >= 10
        return True
    
    def _render_room(self, room: int):
        """Render the specified room."""
        if room == 0:
            self.render_room_0_introduction()
        elif room == 1:
            self.render_room_1_briefing()
        # Add more rooms as needed
    
    def render_room_0_introduction(self):
        """Render the introduction room."""
        self.render_room_markdown(self.rooms_dir / "room_0_introduction.md")
        # Add navigation buttons
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button("Return to start", disabled=True)
        with col_next:
            if st.button("Go to Room 1: Briefing"):
                st.session_state.room_index = 1
                st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 1)
                do_rerun()
    
    def render_room_1_briefing(self):
        """Render the briefing room."""
        self.render_room_markdown(self.rooms_dir / "room_1_briefing.md")
        
        # Add chat interface
        system_prompt = read_markdown_file(self.rooms_dir / "room_1_briefing_system.md") + "\n\n" + self.lore_text
        unlocked = ui_chat_area(
            "briefing",
            system_prompt,
            unlock_field="unlocked",
            assistant_display_transform=json_message_display_transform,
            disable_on_unlock=True,
        )
        
        # Add navigation
        if unlocked:
            st.session_state.max_room_unlocked = max(st.session_state.max_room_unlocked, 2)
        # ... rest of navigation logic
```

#### 4. Update Main App
Add your scenario to `app.py` in the `render_scenario` function:
```python
def render_scenario(scenario_name: str):
    """Generic scenario renderer that loads the appropriate scenario class."""
    scenario_dir = SCENARIOS_DIR / scenario_name
    
    try:
        if scenario_name == "house_price_prediction":
            from scenarios.house_price_prediction.scenario import HousePricePredictionScenario
            scenario = HousePricePredictionScenario(scenario_dir)
            scenario.render_scenario()
        elif scenario_name == "your_scenario_name":  # Add this
            from scenarios.your_scenario_name.scenario import YourScenarioScenario
            scenario = YourScenarioScenario(scenario_dir)
            scenario.render_scenario()
        else:
            st.error(f"Scenario '{scenario_name}' is not yet implemented.")
    except ImportError as e:
        st.error(f"Could not load scenario '{scenario_name}': {e}")
    except Exception as e:
        st.error(f"Error rendering scenario '{scenario_name}': {e}")
```

#### 5. Create Required Content Files

**lore.md** - Scenario metadata and persona definitions:
```markdown
# Project Lore: Your Scenario Name

## 1. Project Background & Data Source
- **Company:** Your company name
- **Business Goal:** Your business objective
- **ML Task:** Classification/Regression/etc.
- **Dataset:** Description of your dataset

## 2. LLM Personas
### Persona A: "The Project Manager"
- **Role:** Description
- **Motivation:** What drives them
- **Behavior:** How they act

### Persona B: "The Data Steward"
- **Role:** Description
- **Motivation:** What drives them
- **Behavior:** How they act

## 3. Dataset Field Descriptions
- **field1:** Description (Type: type)
- **field2:** Description (Type: type)
```

**data/fields.csv** - Field metadata:
```csv
name,description,type,category,is_target
field1,Description of field1,type1,category1,false
field2,Description of field2,type2,category2,true
```

**rooms/room_X_name.md** - Student-facing content
**rooms/room_X_name_system.md** - LLM system prompts

#### 6. Key Features to Implement

**Room Unlock Logic:**
- Override `_is_room_downloads_unlocked()` for custom unlock conditions
- Use `st.session_state` to track progress
- Return `True` for unlocked rooms, `False` for locked

**Download System:**
- Configure files in `download_config.py`
- Files are automatically validated on scenario initialization
- Use `self.render_downloads_for_room(room_number)` to display downloads

**Chat Integration:**
- Use `ui_chat_area()` for LLM interactions
- Provide system prompts from `*_system.md` files
- Use `json_message_display_transform` for clean display

### Best Practices

1. **Inherit from BaseScenario**: Always inherit from `BaseScenario` to get common functionality
2. **Use Download Configuration**: Leverage the download system for file management
3. **Separate Concerns**: Keep game logic in scenario class, file metadata in download config
4. **Follow Naming Conventions**: Use consistent naming for rooms and files
5. **Test Thoroughly**: Test each room and unlock condition
6. **Document Personas**: Clearly define persona behavior in `lore.md`

### Example: Complete Scenario Structure

```
scenarios/customer_churn/
├── __init__.py
├── scenario.py                    # Main scenario logic
├── download_config.py             # Download configuration
├── lore.md                        # Scenario metadata
├── teacher_guide.md               # Teaching guide
├── cheats.md                      # Demo shortcuts
├── data/
│   ├── customer_data.csv         # Main dataset
│   └── fields.csv                # Field metadata
└── rooms/
    ├── room_0_introduction.md
    ├── room_1_briefing.md
    ├── room_1_briefing_system.md
    ├── room_2_discovery.md
    ├── room_2_discovery_system.md
    └── ...                       # More rooms
```

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

