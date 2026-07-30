-- Produce the 56 platform-week rows used for the matched Max-2 comparison.
WITH action_week AS (
  SELECT
    week_start,
    conversion_action_name,
    SUM(conversions) AS conversions,
    SUM(conversion_value) AS conversion_value
  FROM conversion_actions
  WHERE conversion_action_name IN (
    'SR Sales',
    'Google Shopping App Purchase'
  )
  GROUP BY week_start, conversion_action_name
),
platform_weeks AS (
  SELECT
    campaign.week_start,
    campaign.week_end,
    CASE
      WHEN campaign.week_start BETWEEN '2025-01-06' AND '2025-07-14'
        THEN 'WooCommerce'
      WHEN campaign.week_start BETWEEN '2026-01-05' AND '2026-07-13'
        THEN 'Shopify'
    END AS platform,
    campaign.cost,
    campaign.impressions,
    campaign.clicks,
    campaign.interactions,
    action.conversions,
    action.conversion_value,
    action.conversion_value / NULLIF(campaign.cost, 0) AS roas
  FROM weekly_campaign AS campaign
  INNER JOIN action_week AS action
    ON action.week_start = campaign.week_start
   AND action.conversion_action_name = CASE
     WHEN campaign.week_start BETWEEN '2025-01-06' AND '2025-07-14'
       THEN 'SR Sales'
     WHEN campaign.week_start BETWEEN '2026-01-05' AND '2026-07-13'
       THEN 'Google Shopping App Purchase'
   END
  WHERE campaign.week_start BETWEEN '2025-01-06' AND '2025-07-14'
     OR campaign.week_start BETWEEN '2026-01-05' AND '2026-07-13'
)
SELECT
  week_start,
  week_end,
  platform,
  cost,
  impressions,
  clicks,
  interactions,
  conversions,
  conversion_value,
  roas
FROM platform_weeks
ORDER BY platform, week_start;
