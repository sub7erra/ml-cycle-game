# House Price Prediction — Cheats for Testing

Use these example student messages to reliably progress through rooms during testing.

## Room 1: Project Briefing

Paste one complete plan (single message) that hits all criteria.

```
Project plan:
- ML task: This is a regression problem because the target is a continuous price.
- Success metric: We'll use MAPE (a relative error) so mistakes scale with listing price. Absolute errors like MAE over-penalize low-price homes and under-penalize high-price homes.
- Non-ML baseline: A simple price-per-sqft heuristic or a manual agent appraisal can serve as an initial baseline.
```

## Room 2: Data Discovery

Ask for at least 10 specific fields by exact name or by clear description.

```
Do you have yr_built?
Do you have sqft_living?
Do you have zipcode?
Do you have bedrooms?
Do you have bathrooms?
Do you have sqft_lot?
Do you have sqft_above?
Do you have sqft_basement?
Do you have view?
Do you have grade?
```

(Alternatively, ask for groups and then say "all of these" to confirm multiple.)

## Room 3: EDA Findings

Provide method, numeric evidence, and interpretation.

```
Top predictor: sqft_living.
Method: computed Pearson correlation and inspected scatter plots.
Evidence: Pearson r ≈ 0.70 between sqft_living and price; grade is second at ≈ 0.66.
Interpretation: larger living area is associated with higher sale price in a roughly positive linear trend.
```

## Room 4: Feature Engineering

Propose features one-by-one with plain-language hypotheses until you reach ≥30 points.

```
Feature: bath_per_bed
Hypothesis: This captures day-to-day convenience. A 4-bed home with 1 bath is frustrating for families; better ratios should increase price.
```

```
Feature: zipcode_price_mean
Hypothesis: Neighborhoods have their own price levels due to schools and amenities. Using the average price per zipcode adds that location signal.
```

(If needed)
```
Feature: living_vs_lot_ratio
Hypothesis: Trade-off between indoor and outdoor space. Higher ratios suggest low-maintenance living that many buyers value.
```

## Room 5: Final Submission

- Deselect id and date.
- Ensure redundancy is minimized (e.g., if you engineered has_basement, consider dropping sqft_basement).
