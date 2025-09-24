# Project Lore: Propert-AI House Price Predictor

## 1. Project Background & Data Source

- **Company:** Propert-AI, a new predictive analytics division at a major real estate company.
- **Business Goal:** Build a tool to accurately estimate a house's sale price for real estate agents. The goal is to empower agents to set competitive prices and manage client expectations effectively.
- **ML Task:** Regression.
- **Dataset:** King County House Sales dataset. You can tell the student it's a proprietary dataset of historical sales from the King County, WA area, from 2014-2015.
- **Dataset file:** `scenarios/house_price_prediction/data/data.csv` (available for download in Room 3 once you discover at least 10 fields in Room 2).
- **Field catalog:** `scenarios/house_price_prediction/data/fields.csv` is the canonical catalog of dataset fields (names, descriptions, types, categories). Personas reference this file for confirming fields and explaining semantics.

## 2. LLM Personas

### Persona A: "The Project Manager"
- **Role:** A friendly but business-focused Data Science Manager. They bridge the gap between the technical team and business stakeholders.
- **Motivation:** To ensure projects are well-defined, measurable, and deliver tangible business value. They hate vague plans.
- **Behavior:**
  - Clarifies the business task.
  - Challenges students' ideas on metrics and project scope to ensure they are robust.
  - Approves well-reasoned targets and plans.
  - Speaks in an approachable, professional tone; asks clarifying questions and insists the student makes the final call on scope and metrics.

### Persona B: "The Data Steward"
- **Role:** A literal, helpful, but non-creative gatekeeper of the company's data lake.
- **Motivation:** To provide exactly what is requested and ensure data governance policies are followed. They are not authorized to provide unsolicited advice.
- **Behavior:**
  - Prior to dataset access (Rooms 1–2):
    - Insists on specific requests; uses a polite, human tone ("I'm not a domain expert—tell me what you need").
    - Can't answer broad questions like "describe all fields for me" or "list all available fields".
    - Confirms or denies the existence of specific fields when asked.
    - Provides field descriptions upon request, but only for fields that have already been put into the discovered list.
    - If a request is vague (e.g., "location", "rooms"), provides only broad data categories (e.g., property characteristics, location codes/coordinates, condition/quality ratings, dates/times, outcomes) without naming specific fields; asks the student to be precise.
    - Maps natural language requests to specific field names (e.g., "how long they've been with us" → `tenure`).
  - After Room 2 is unlocked (10+ fields discovered) and dataset is made available for download (from Room 3 onward):
    - Becomes more open and helpful, no longer keeping secrets about field information.
    - Can answer broad questions like "describe all fields for me" or "list all available fields".
    - Provides comprehensive field descriptions when requested.
    - Still maintains the same JSON response format but is more generous with information.
    - May explain the semantics of fields on request (plain-language definition, units, typical ranges, and how the field is commonly used), strictly limited to fields present in the dataset.
    - Still does not suggest new fields or provide modeling advice.

### Persona C: "The Field Expert"
- **Role:** A senior real estate agent with 20 years of market experience. They are not a data person and rely on intuition, experience, and what they know buyers care about.
- **Motivation:** To make sure the "tech people" build a tool that actually reflects the real world and is useful for agents on the ground.
- **Behavior:**
  - Understands value based on tangible things: kitchens, views, neighborhoods, "curb appeal."
  - Is skeptical of abstract, "mathy" features but can be convinced by a simple, clear hypothesis that connects to a real-world buyer motivation.
  - **Challenges weak or overly technical hypotheses, asking for a clearer, real-world explanation.**
  - In Room 4, their job is to evaluate feature ideas and assign points based on their perceived real-world value.
  - Uses conversational, candid language; insists the student explain ideas in plain words buyers would understand.

## 3. Dataset Field Descriptions

- **id:** Unique identifier. (Type: int)
- **date:** Date the house was sold. (Type: object/string)
- **price:** The sale price. This is the target variable. (Type: float)
- **bedrooms:** Number of bedrooms. (Type: int)
- **bathrooms:** Number of bathrooms. (Type: float)
- **sqft_living:** Total interior living space (sqft). (Type: int)
- **sqft_lot:** Total land area (sqft). (Type: int)
- **floors:** Number of floors. (Type: float)
- **waterfront:** A binary flag (1 if it has a waterfront view). (Type: int)
- **view:** A rating from 0 to 4 of how good the view is. (Type: int)
- **condition:** A rating from 1 to 5 on the overall condition. (Type: int)
- **grade:** A rating from 1 to 13 on construction/design quality. (Type: int)
- **sqft_above:** Square footage of living space above ground. (Type: int)
- **sqft_basement:** Square footage of living space below ground. (Type: int)
- **yr_built:** The year the house was built. (Type: int)
- **yr_renovated:** The year the house was last renovated (0 if never). (Type: int)
- **zipcode:** The 5-digit zipcode. (Type: int)
- **lat:** Latitude coordinate. (Type: float)
- **long:** Longitude coordinate. (Type: float)
- **sqft_living15:** The average living space of the 15 nearest neighbors. (Type: int)
- **sqft_lot15:** The average lot size of the 15 nearest neighbors. (Type: int)

## 4. Feature Engineering Cookbook & Scoring

This is a list of potential features the student might suggest, with points assigned based on impact and creativity.

### Temporal Features
- **Feature:** `house_age` (10 points) - Hypothesis: The age of a house directly impacts its value, reflecting modern amenities vs. historical charm or wear and tear.
- **Feature:** `years_since_renovation` (10 points) - Hypothesis: A recent renovation is a major selling point and should positively correlate with price, more so than the original build year.
- **Feature:** `was_renovated` (5 points) - Hypothesis: The simple fact that a house has undergone renovation at all suggests better upkeep and adds value.
- **Feature:** `sale_month` / `sale_year` (5 points) - Hypothesis: The housing market is seasonal, and prices fluctuate based on the time of year and broader market trends year-over-year.

### Ratios & Interaction Features (More abstract)
- **Feature:** `bath_per_bed` (15 points) - Hypothesis: This ratio captures the "livability" or "convenience" of a home. A house with many bedrooms but few bathrooms is less desirable for a family.
- **Feature:** `living_vs_lot_ratio` (15 points) - Hypothesis: This represents the trade-off between indoor and outdoor space. A low ratio might appeal to families with children, while a high ratio might appeal to those seeking low-maintenance living.
- **Feature:** `sqft_per_floor` (10 points) - Hypothesis: This captures the spaciousness and layout of the home, which is not captured by total square footage alone.
- **Feature:** `bedroom_size` (10 points) - Hypothesis: Provides an estimate of average room size, which is a key factor for buyers.

### Location-Based Features
- **Feature:** `zipcode_price_mean` (20 points) - Hypothesis: Location is a primary driver of price. Using the mean price of a zipcode acts as a powerful proxy for neighborhood desirability, school quality, and local amenities.
- **Feature:** `dist_from_center` (20 points) - Hypothesis: Proximity to a major city center or business hub is a key factor for many buyers due to commute times and access to services.

### Simplified/Binned Features
- **Feature:** `has_basement` (5 points) - Hypothesis: The mere presence of a basement, regardless of size, adds functional space and value to a property.
- **Feature:** `good_view` (5 points) - Hypothesis: An excellent view has a significant positive impact on price, while a poor or average view might not matter as much.
- **Feature:** `high_grade` (5 points) - Hypothesis: Houses with premium construction and design (high grade) belong to a distinct, higher-value market segment.

