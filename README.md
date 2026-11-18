# DA-02 Customer 360 and Marketing Attribution

dbt project on BigQuery that builds a customer view from the GA4 sample e-commerce data, scores customers with RFM, and compares four attribution models to see which channels bring in revenue.

## Data

- Real: the GA4 obfuscated sample dataset (`bigquery-public-data.ga4_obfuscated_sample_ecommerce`, Nov 2020 to Jan 2021). Sessions, purchases, revenue and per-session source/medium/campaign all come from it.
- Simulated: CRM customers, the device-to-customer mapping, and ad spend. They are generated in SQL by hashing user ids, so the same run always gives the same result.
  - about 35% of buyers are matched to a CRM customer, and some customers have more than one device
  - spend is real daily sessions per channel times an assumed cost per session (set in `dbt_project.yml`), with some daily noise

## Models

- `stg_events`, `sessions`, `orders`: cleaned GA4 data. Source/medium is mapped to a channel by the `classify_channel` macro (Paid Search, Organic Search, Affiliate, Referral, Direct). Traffic from the store's own domain is labelled Internal and gets no credit. Missing or hidden sources are Unattributed.
- `identity_map`, `synthetic_crm_customers`, `customer_profile`: the simulated CRM and one row per customer.
- `attribution_touchpoints`, `attribution_long`: each order's sessions in the 30 days before purchase, credited by first touch, last touch, linear and time decay (7 day half-life). Orders with no usable touch go to Unattributed so revenue still adds up.
- `mart_rfm`, `mart_rfm_segments`: recency, frequency and monetary scores (1 to 5) and the segments Champions, Loyal, Recent, At Risk, Needs Attention, Lost.
- `mart_attribution_compare`, `mart_channel_roi`, `mart_campaign_roi`, `mart_budget_signals`: revenue, ROI and cost per order by channel and model.

Tests check that every model distributes exactly the total revenue, that weights sum to 1 per order, and that first and last touch actually differ.

## Setup

BigQuery sandbox is enough, no billing account needed.

```
pip install -r requirements.txt
gcloud auth application-default login
cp profiles.yml.example ~/.dbt/profiles.yml
dbt debug
dbt run
dbt test
```

Put your project id in `profiles.yml`. For a quick run on two weeks of data: `dbt run --vars '{end_suffix: "20201114"}'`.

Export the marts for Tableau and the website:

```
export GCP_PROJECT=your-project-id
python scripts/export_marts.py
```

## Limitations

- Three months of data, so the 30 day lookback is cut short for November orders.
- Only about a quarter of buyers touch more than one channel. For the rest, all four models give the same answer.
- Ad spend is simulated, so the ROI figures show the method rather than real returns.
- The sandbox expires tables after 60 days and has no DML, so every model is a full-refresh table.
