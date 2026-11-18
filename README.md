# data-analytics-portfolio

Final projects for the Nexvia data analytics track.

- `DA-02-customer-360-attribution`: GA4 web data and a simulated CRM combined into a customer view, with four attribution models and channel ROI. dbt, BigQuery, SQL, Tableau.
- `DA-03-retail-supply-chain-control-tower`: hourly inventory, delivery and supplier monitoring with anomaly alerts and a demand forecast. PostgreSQL, Airflow, Python, Prophet, Superset, Docker.

Each folder has its own README with setup steps.

Live site: add the Vercel URL here

Both projects use public datasets. Anything simulated (CRM records, ad spend, suppliers, inventory) is listed in the project READMEs.

The `web/` folder is the Next.js site deployed on Vercel. It reads exported JSON from `web/public/data`.
