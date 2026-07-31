# Shopify And Merchant Center Category Precedence

## Status

Documented for future cleanup. This finding does not block the current product
segmentation and custom-label work.

## Question

Does the Shopify product metafield
`mm-google-shopping.google_product_category` reach Google Merchant Center
through the Google & YouTube app?

## Finding

Yes, but it behaves as a fallback rather than the authoritative category.

Observed precedence:

```text
Shopify standard product category, when populated
  -> mm-google-shopping.google_product_category
  -> Merchant Center processed google_product_category
```

When Shopify's standard product category was absent or effectively
uncategorized, Merchant Center used the value from
`mm-google-shopping.google_product_category`. When a Shopify standard category
was populated, Merchant Center used that category instead.

## Read-Only Verification

The July 30, 2026 audit:

- scanned `15,797` Shopify products
- found `10,190` products with
  `mm-google-shopping.google_product_category`
- found no mapped SR product types missing the metafield
- compared Shopify product and variant IDs to processed products from Merchant
  Center data source `Shopify App API` (`10580915723`)
- sampled `20` tiebacks and found `20/20` exact matches to the
  `mm-google-shopping` category
- sampled `20` rugs and found `20/20` exact matches to the
  `mm-google-shopping` category
- checked all `27` products with SR product type `kimonos` and found `27/27`
  used the Shopify standard category rather than the more-specific
  `mm-google-shopping` category

No Shopify or Merchant Center data was changed during verification.

## Example Conflict

For one kimono-family product, the derived metafield contained:

```text
Apparel & Accessories > Clothing > Traditional & Ceremonial Clothing >
Kimonos > Tomesode & Houmongi Kimonos
```

The Shopify standard category, and therefore the processed Merchant Center
category, was:

```text
Apparel & Accessories > Clothing > Traditional & Ceremonial Clothing > Kimonos
```

Other kimono-family products were categorized in Shopify as traditional
clothing accessories, which also took precedence over the derived metafield.

## Future Category Cleanup

Treat Shopify standard product categories as the likely long-term source of
truth because the Google & YouTube app gives them precedence.

Future work should:

1. Audit Shopify standard-category coverage and accuracy by SR product type.
2. Decide the intended standard category for kimonos, obi belts, haori
   jackets, and other products currently grouped under SR type `kimonos`.
3. Populate or correct Shopify standard categories in a reviewed batch.
4. Recheck the resulting processed Merchant Center categories.
5. Decide whether
   `update-google-product-category-from-sr-product-type` remains useful as a
   fallback, should validate category conflicts, or can eventually be retired.
6. Review the small set of legacy numeric `mm-google-shopping` values separately
   rather than assuming they follow the current mapping.

Do not combine this cleanup with the current segmentation rollout. Merchant
Center custom labels and their Shopify source fields can be designed and
implemented independently.

