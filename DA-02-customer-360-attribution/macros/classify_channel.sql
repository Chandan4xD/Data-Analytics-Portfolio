{% macro classify_channel(src, med) %}
CASE
  WHEN REGEXP_CONTAINS(IFNULL({{ src }}, ''), r'googlemerchandisestore\.com') THEN 'Internal'
  WHEN {{ med }} = 'cpc'       THEN 'Paid Search'
  WHEN {{ med }} = 'organic'   THEN 'Organic Search'
  WHEN {{ med }} = 'affiliate' THEN 'Affiliate'
  WHEN {{ med }} = 'referral'  THEN 'Referral'
  WHEN {{ src }} = '(direct)'  THEN 'Direct'
  ELSE 'Unattributed'
END
{% endmacro %}
