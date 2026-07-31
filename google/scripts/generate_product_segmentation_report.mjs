import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

function argumentValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = argumentValue("--workspace-root") ?? path.resolve(scriptDir, "../../..");
const inputPath = argumentValue("--input");
const outputPath = argumentValue("--output");
if (!inputPath || !outputPath) {
  throw new Error(
    "Usage: generate_product_segmentation_report.mjs --input <Google Ads .xlsx> --output <combined .xlsx>",
  );
}
const outputDir = path.dirname(outputPath);
const previewDir = argumentValue("--preview-dir") ?? path.join(os.tmpdir(), "sr-product-segmentation-previews");
const artifactToolModule =
  process.env.ARTIFACT_TOOL_MODULE ??
  "/Users/marcin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { FileBlob, SpreadsheetFile, Workbook } = await import(
  pathToFileURL(artifactToolModule).href
);
const shopifyPython = `${workspaceRoot}/sr-automation/.venv/bin/python`;
const shopifyQueryScript = `${workspaceRoot}/sr-ads/google/scripts/query_shopify_order_types.py`;

const imported = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const importedSheet = imported.worksheets.getItem("Sheet0");
const sourceValues = importedSheet.getRange("A1:T4038").values;
const dateRange = sourceValues[1][0];
const dataRows = sourceValues.slice(3);
const n = (v) => typeof v === "number" && Number.isFinite(v) ? v : 0;

const records = dataRows.map((r, index) => {
  const itemId = String(r[2] ?? "");
  const match = itemId.match(/^shopify_[^_]+_(\d+)_(\d+)$/i);
  const cost = n(r[10]);
  const conversions = n(r[12]);
  const value = n(r[13]);
  const reportedRoas = n(r[14]);
  return {
    sourceRow: index + 4,
    title: String(r[1] ?? ""),
    itemId,
    productId: match?.[1] ?? itemId,
    variantId: match?.[2] ?? "",
    cost,
    conversions,
    value,
    reportedRoas,
    roas: cost > 0 ? value / cost : 0,
    cpa: conversions > 0 ? cost / conversions : 0,
    gap: Math.max(0, cost - value),
  };
});

const totals = records.reduce(
  (a, r) => {
    a.cost += r.cost;
    a.conversions += r.conversions;
    a.value += r.value;
    return a;
  },
  { cost: 0, conversions: 0, value: 0 },
);
const overallCpa = totals.cost / totals.conversions;
const significantSpend = 2 * overallCpa;

const lookupDir = await fs.mkdtemp(path.join(os.tmpdir(), "sr-product-order-types-"));
const lookupIdsPath = path.join(lookupDir, "product-gids.json");
const lookupOutputPath = path.join(lookupDir, "shopify-order-types.json");
await fs.writeFile(
  lookupIdsPath,
  JSON.stringify(records.map((record) => `gid://shopify/Product/${record.productId}`)),
  "utf8",
);
execFileSync(
  shopifyPython,
  [
    shopifyQueryScript,
    "--ids-file",
    lookupIdsPath,
    "--output",
    lookupOutputPath,
  ],
  { cwd: workspaceRoot, stdio: "inherit" },
);
const shopifyLookup = JSON.parse(await fs.readFile(lookupOutputPath, "utf8"));
for (const record of records) {
  const gid = `gid://shopify/Product/${record.productId}`;
  const shopify = shopifyLookup.products[gid] ?? {};
  record.orderType = shopify.order_type ?? "not_found";
  record.totalInventory = shopify.total_inventory ?? null;
}
const shopifyCoverage = records.filter((record) => record.orderType !== "not_found").length;

const performanceExclude = records
  .filter((r) => r.cost >= significantSpend && r.roas < 1)
  .sort((a, b) => b.gap - a.gap);
const performanceExcludeSet = new Set(performanceExclude.map((r) => r.itemId));
const zeroRoas = records
  .filter((r) => r.cost >= 100 && r.reportedRoas === 0)
  .sort((a, b) => b.cost - a.cost);
const zeroAdditional = zeroRoas.filter((r) => !performanceExcludeSet.has(r.itemId));
const zeroAdditionalSet = new Set(zeroAdditional.map((r) => r.itemId));
const excludeNow = [...performanceExclude, ...zeroAdditional]
  .sort((a, b) => b.gap - a.gap);
const marginReview = records
  .filter((r) => r.cost >= significantSpend && r.roas >= 1 && r.roas < 2)
  .sort((a, b) => a.roas - b.roas);
const canonicalOrderTypes = [
  "standard",
  "special",
  "special-2",
  "custom",
  "consultation",
  "sewing",
  "unassigned",
  "not_found",
];
const observedOrderTypes = new Set(records.map((record) => record.orderType));
const orderTypes = [
  ...canonicalOrderTypes.filter((value) => observedOrderTypes.has(value)),
  ...[...observedOrderTypes]
    .filter((value) => !canonicalOrderTypes.includes(value))
    .sort(),
];

const actionQueue = [
  ...excludeNow.map((r) => ({
    ...r,
    action: "Exclude now",
    reason: zeroAdditionalSet.has(r.itemId)
      ? "Spend ≥ $100 and reported ROAS = 0"
      : "Spend ≥ 2× CPA and ROAS < 1.0",
  })),
  ...marginReview.map((r) => ({ ...r, action: "Margin review", reason: "Spend ≥ 2× CPA and ROAS between 1.0 and 2.0" })),
];

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const queue = workbook.worksheets.add("Action Queue");
const exclude = workbook.worksheets.add("Exclude Now");
const margin = workbook.worksheets.add("Margin Review");
const source = workbook.worksheets.add("Source Data");

const colors = {
  navy: "#17324D",
  blue: "#2F75B5",
  lightBlue: "#D9EAF7",
  red: "#C00000",
  lightRed: "#FCE4E4",
  amber: "#BF7A00",
  lightAmber: "#FFF1CC",
  green: "#2E7D32",
  lightGreen: "#E2F0D9",
  gray: "#666666",
  lightGray: "#F2F2F2",
  white: "#FFFFFF",
  border: "#D9E1F2",
};

const titleStyle = {
  fill: colors.navy,
  font: { bold: true, color: colors.white, size: 18 },
  verticalAlignment: "center",
};
const sectionStyle = {
  fill: colors.lightBlue,
  font: { bold: true, color: colors.navy, size: 11 },
  borders: { preset: "outside", style: "thin", color: colors.border },
};
const headerStyle = {
  fill: colors.navy,
  font: { bold: true, color: colors.white },
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "all", style: "thin", color: colors.border },
};

// Source data: preserve every exported value unchanged.
source.getRange("A1:T4038").values = sourceValues;
source.getRange("U3").values = [["Shopify Order Type"]];
source.getRange("U4:U4038").values = records.map((record) => [record.orderType]);
source.getRange("A1:U1").merge();
source.getRange("A1:U1").format = titleStyle;
source.getRange("A1:U1").format.rowHeight = 28;
source.getRange("A2:U2").merge();
source.getRange("A2:U2").format = {
  fill: colors.lightBlue,
  font: { italic: true, color: colors.navy },
};
source.getRange("A3:U3").format = headerStyle;
source.freezePanes.freezeRows(3);
source.getRange("A:A").format.columnWidth = 18;
source.getRange("B:B").format.columnWidth = 48;
source.getRange("C:C").format.columnWidth = 34;
source.getRange("D:E").format.columnWidth = 14;
source.getRange("F:T").format.columnWidth = 13;
source.getRange("U:U").format.columnWidth = 18;
source.getRange("F4:F4038").format.numberFormat = "$#,##0.00";
source.getRange("G4:H4038").format.numberFormat = "#,##0";
source.getRange("I4:I4038").format.numberFormat = "0.00%";
source.getRange("K4:L4038").format.numberFormat = "$#,##0.00";
source.getRange("M4:M4038").format.numberFormat = "0.00";
source.getRange("N4:N4038").format.numberFormat = "$#,##0.00";
source.getRange("O4:O4038").format.numberFormat = "0.00x";
source.getRange("P4:P4038").format.numberFormat = "$#,##0.00";
source.getRange("Q4:Q4038").format.numberFormat = "0.00%";
source.getRange("R4:R4038").format.numberFormat = "$#,##0.00";
source.getRange("S4:S4038").format.numberFormat = "$#,##0.00";
const sourceTable = source.tables.add("A3:U4038", true, "SourceDataTable");
sourceTable.style = "TableStyleMedium2";

function setupListSheet(sheet, title, subtitle, rows, actionResolver) {
  sheet.showGridLines = false;
  sheet.getRange("A1:N1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:N1").format = titleStyle;
  sheet.getRange("A1:N1").format.rowHeight = 30;
  sheet.getRange("A2:N2").merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2:N2").format = {
    fill: colors.lightBlue,
    font: { color: colors.navy, italic: true },
    wrapText: true,
  };
  sheet.getRange("A2:N2").format.rowHeight = 32;
  const headers = [["Rank", "Action", "Shopify Product GID", "Google Item ID", "Order Type", "Product", "Source row", "Cost", "Conversions", "Conv. value", "ROAS", "CPA", "Cost − value", "Reason"]];
  sheet.getRange("A4:N4").values = headers;
  sheet.getRange("A4:N4").format = headerStyle;

  rows.forEach((record, idx) => {
    const row = idx + 5;
    const actionData = actionResolver(record, idx);
    sheet.getRange(`A${row}:C${row}`).values = [[idx + 1, actionData.action, `gid://shopify/Product/${record.productId}`]];
    sheet.getRange(`D${row}:F${row}`).formulas = [[
      `='Source Data'!C${record.sourceRow}`,
      `='Source Data'!U${record.sourceRow}`,
      `='Source Data'!B${record.sourceRow}`,
    ]];
    sheet.getRange(`G${row}`).values = [[record.sourceRow]];
    sheet.getRange(`H${row}:J${row}`).formulas = [[
      `='Source Data'!K${record.sourceRow}`,
      `='Source Data'!M${record.sourceRow}`,
      `='Source Data'!N${record.sourceRow}`,
    ]];
    sheet.getRange(`K${row}`).formulas = [[`=IFERROR(J${row}/H${row},0)`]];
    sheet.getRange(`L${row}`).formulas = [[`=IFERROR(H${row}/I${row},0)`]];
    sheet.getRange(`M${row}`).formulas = [[`=MAX(0,H${row}-J${row})`]];
    sheet.getRange(`N${row}`).values = [[actionData.reason]];
  });

  const endRow = Math.max(5, rows.length + 4);
  sheet.getRange(`H5:H${endRow}`).format.numberFormat = "$#,##0.00";
  sheet.getRange(`I5:I${endRow}`).format.numberFormat = "0.00";
  sheet.getRange(`J5:J${endRow}`).format.numberFormat = "$#,##0.00";
  sheet.getRange(`K5:K${endRow}`).format.numberFormat = "0.00x";
  sheet.getRange(`L5:M${endRow}`).format.numberFormat = "$#,##0.00";
  sheet.getRange(`A4:N${endRow}`).format.borders = { preset: "all", style: "thin", color: colors.border };
  sheet.getRange(`A5:N${endRow}`).format.wrapText = false;
  sheet.getRange("A:A").format.columnWidth = 8;
  sheet.getRange("B:B").format.columnWidth = 20;
  sheet.getRange("C:C").format.columnWidth = 32;
  sheet.getRange("C:C").format.numberFormat = "@";
  sheet.getRange("D:D").format.columnWidth = 38;
  sheet.getRange("D:D").format.numberFormat = "@";
  sheet.getRange("E:E").format.columnWidth = 14;
  sheet.getRange("F:F").format.columnWidth = 48;
  sheet.getRange("G:G").format.columnWidth = 11;
  sheet.getRange("H:M").format.columnWidth = 14;
  sheet.getRange("N:N").format.columnWidth = 45;
  sheet.getRange(`F5:F${endRow}`).format.wrapText = true;
  sheet.getRange(`N5:N${endRow}`).format.wrapText = true;
  sheet.freezePanes.freezeRows(4);

  if (rows.length > 0) {
    const table = sheet.tables.add(`A4:N${endRow}`, true, `${sheet.name.replaceAll(" ", "")}Table`);
    table.style = "TableStyleMedium2";
  }
  return endRow;
}

const queueEnd = setupListSheet(
  queue,
  "Google Ads Product Action Queue",
  "Deduplicated YTD action list. Exclusion is based on purchase conversion value, not “All conversions.”",
  actionQueue,
  (r) => ({ action: r.action, reason: r.reason }),
);
const excludeEnd = setupListSheet(
  exclude,
  "Exclude Now",
  `Rules: cost ≥ 2× overall CPA ($${significantSpend.toFixed(2)}) and purchase ROAS < 1.0, or cost ≥ $100 with reported ROAS = 0.`,
  excludeNow,
  (r) => ({
    action: "Exclude",
    reason: zeroAdditionalSet.has(r.itemId)
      ? "Meaningful spend with no measurable purchase return"
      : "High spend and conversion value below ad cost",
  }),
);
const marginEnd = setupListSheet(
  margin,
  "Margin Review: ROAS 1.0–2.0",
  `Rule: cost ≥ 2× overall CPA ($${significantSpend.toFixed(2)}) and purchase ROAS from 1.0 to below 2.0.`,
  marginReview,
  () => ({ action: "Review margin", reason: "Revenue exceeds ad cost, but likely not product and fulfillment cost" }),
);

// Summary/dashboard.
summary.showGridLines = false;
summary.getRange("A1:J1").merge();
summary.getRange("A1").values = [["Google Ads Product Segmentation Report"]];
summary.getRange("A1:J1").format = titleStyle;
summary.getRange("A1:J1").format.rowHeight = 32;
summary.getRange("A2:J2").merge();
summary.getRange("A2").values = [[`${dateRange} · Source: Google Ads product report`]];
summary.getRange("A2:J2").format = {
  fill: colors.lightBlue,
  font: { color: colors.navy, italic: true },
};

summary.getRange("A4:J4").merge();
summary.getRange("A4").values = [["Account performance"]];
summary.getRange("A4:J4").format = sectionStyle;
summary.getRange("A5:B5").values = [["Spend", null]];
summary.getRange("C5:D5").values = [["Conversions", null]];
summary.getRange("E5:F5").values = [["Conversion value", null]];
summary.getRange("G5:H5").values = [["Purchase ROAS", null]];
summary.getRange("I5:J5").values = [["Purchase CPA", null]];
for (const range of ["A5:B5", "C5:D5", "E5:F5", "G5:H5", "I5:J5"]) {
  summary.getRange(range).merge();
  summary.getRange(range).format = {
    fill: colors.lightGray,
    font: { bold: true, color: colors.gray },
    horizontalAlignment: "center",
  };
}
summary.getRange("A6:B6").merge();
summary.getRange("A6").formulas = [["=SUM('Source Data'!K4:K4038)"]];
summary.getRange("C6:D6").merge();
summary.getRange("C6").formulas = [["=SUM('Source Data'!M4:M4038)"]];
summary.getRange("E6:F6").merge();
summary.getRange("E6").formulas = [["=SUM('Source Data'!N4:N4038)"]];
summary.getRange("G6:H6").merge();
summary.getRange("G6").formulas = [["=IFERROR(E6/A6,0)"]];
summary.getRange("I6:J6").merge();
summary.getRange("I6").formulas = [["=IFERROR(A6/C6,0)"]];
summary.getRange("A6:B6").format.numberFormat = "$#,##0";
summary.getRange("C6:D6").format.numberFormat = "0.00";
summary.getRange("E6:F6").format.numberFormat = "$#,##0";
summary.getRange("G6:H6").format.numberFormat = "0.00x";
summary.getRange("I6:J6").format.numberFormat = "$#,##0.00";
summary.getRange("A6:J6").format = {
  fill: colors.white,
  font: { bold: true, color: colors.navy, size: 16 },
  horizontalAlignment: "center",
  borders: { preset: "all", style: "thin", color: colors.border },
};

summary.getRange("A8:J8").merge();
summary.getRange("A8").values = [["Rules and thresholds"]];
summary.getRange("A8:J8").format = sectionStyle;
summary.getRange("A9:E12").values = [
  ["Rule", "Threshold", "Purpose", null, null],
  ["Significant spend", null, "2× overall purchase CPA", null, null],
  ["Zero-ROAS exclusion", 100, "Reported ROAS = 0.00", null, null],
  ["Margin review ceiling", 2, "ROAS below this may be unprofitable after COGS", null, null],
];
summary.getRange("B10").formulas = [["=I6*2"]];
summary.getRange("B10:B11").format.numberFormat = "$#,##0.00";
summary.getRange("B12").format.numberFormat = "0.00x";
summary.getRange("A9:E9").format = headerStyle;
summary.getRange("A9:E12").format.borders = { preset: "all", style: "thin", color: colors.border };
summary.getRange("C10:E12").merge(true);

summary.getRange("A14:J14").merge();
summary.getRange("A14").values = [["Action summary"]];
summary.getRange("A14:J14").format = sectionStyle;
summary.getRange("A15:E15").values = [["Bucket", "Unique products", "Spend", "Conversion value", "ROAS"]];
summary.getRange("A15:E15").format = headerStyle;
summary.getRange("A16:A18").values = [
  ["Exclude now"],
  ["Margin review"],
  ["Total action queue"],
];
summary.getRange("B16").values = [[excludeNow.length]];
summary.getRange("B17").values = [[marginReview.length]];
summary.getRange("B18").formulas = [["=SUM(B16:B17)"]];
summary.getRange("C16").formulas = [[`=SUM('Exclude Now'!H5:H${excludeEnd})`]];
summary.getRange("D16").formulas = [[`=SUM('Exclude Now'!J5:J${excludeEnd})`]];
summary.getRange("E16").formulas = [["=IFERROR(D16/C16,0)"]];
summary.getRange("C17").formulas = [[`=SUM('Margin Review'!H5:H${marginEnd})`]];
summary.getRange("D17").formulas = [[`=SUM('Margin Review'!J5:J${marginEnd})`]];
summary.getRange("E17").formulas = [["=IFERROR(D17/C17,0)"]];
summary.getRange("C18").formulas = [["=SUM(C16:C17)"]];
summary.getRange("D18").formulas = [["=SUM(D16:D17)"]];
summary.getRange("E18").formulas = [["=IFERROR(D18/C18,0)"]];
summary.getRange("C16:D18").format.numberFormat = "$#,##0.00";
summary.getRange("E16:E18").format.numberFormat = "0.00x";
summary.getRange("A15:E18").format.borders = { preset: "all", style: "thin", color: colors.border };
summary.getRange("A16:E16").format.fill = colors.lightRed;
summary.getRange("A17:E17").format.fill = colors.lightAmber;
summary.getRange("A18:E18").format = {
  fill: colors.lightBlue,
  font: { bold: true, color: colors.navy },
  borders: { preset: "doubleBottom", style: "thin", color: colors.navy },
};

summary.getRange("G9:J9").merge();
summary.getRange("G9").values = [["Interpretation"]];
summary.getRange("G9:J9").format = headerStyle;
summary.getRange("G10:J13").merge();
summary.getRange("G10").values = [[
  "ROAS below 1.0 means tracked purchase revenue is below advertising cost before product cost, fulfillment, and overhead. Products between 1.0× and 2.0× require margin review. Drop-ship products generally need a higher break-even ROAS."
]];
summary.getRange("G10:J13").format = {
  fill: colors.lightGray,
  wrapText: true,
  verticalAlignment: "top",
  borders: { preset: "all", style: "thin", color: colors.border },
};
summary.getRange("G15:J15").merge();
summary.getRange("G15").values = [["Important caveat"]];
summary.getRange("G15:J15").format = headerStyle;
summary.getRange("G16:J19").merge();
summary.getRange("G16").values = [[
  "Some conversions appear to be low-value sample orders. If samples reliably produce later full-yard purchases outside Google’s attribution window, direct product ROAS understates lifetime value. Treat exclusions as reversible and review after 60–90 days."
]];
summary.getRange("G16:J19").format = {
  fill: colors.lightAmber,
  wrapText: true,
  verticalAlignment: "top",
  borders: { preset: "all", style: "thin", color: colors.amber },
};
summary.getRange("A21:J21").merge();
summary.getRange("A21").values = [["Recommended Shopify mapping"]];
summary.getRange("A21:J21").format = sectionStyle;
summary.getRange("A22:J25").values = [
  ["Metafield", "Value", "Use", null, null, null, null, null, null, null],
  ["custom.ad_status", "exclude", "For products in Exclude Now", null, null, null, null, null, null, null],
  ["custom.ad_exclusion_reason", "poor_direct_roas", "Preserves the reason for automation and review", null, null, null, null, null, null, null],
  ["Review cadence", "60–90 days", "Re-enable products if downstream value justifies it", null, null, null, null, null, null, null],
];
summary.getRange("A22:C22").format = headerStyle;
summary.getRange("A22:C25").format.borders = { preset: "all", style: "thin", color: colors.border };
summary.getRange("C23:J25").merge(true);

summary.getRange("A27:J27").merge();
summary.getRange("A27").values = [["Shopify order-type enrichment"]];
summary.getRange("A27:J27").format = sectionStyle;
summary.getRange("A28:D28").values = [["Order type", "Catalog products", "Action queue", "Exclude now"]];
summary.getRange("A28:D28").format = headerStyle;
orderTypes.forEach((orderType, index) => {
  const row = 29 + index;
  summary.getRange(`A${row}`).values = [[orderType]];
  summary.getRange(`B${row}`).formulas = [[`=COUNTIF('Source Data'!U4:U4038,A${row})`]];
  summary.getRange(`C${row}`).formulas = [[`=COUNTIF('Action Queue'!E5:E${queueEnd},A${row})`]];
  summary.getRange(`D${row}`).formulas = [[`=COUNTIF('Exclude Now'!E5:E${excludeEnd},A${row})`]];
});
const orderTypeEndRow = 28 + orderTypes.length;
summary.getRange(`A28:D${orderTypeEndRow}`).format.borders = { preset: "all", style: "thin", color: colors.border };
summary.getRange("F28:J28").merge();
summary.getRange("F28").values = [["Shopify lookup status"]];
summary.getRange("F28:J28").format = headerStyle;
summary.getRange("F29:J31").merge();
summary.getRange("F29").values = [[
  `${shopifyCoverage.toLocaleString()} of ${records.length.toLocaleString()} Google Ads products resolved in Shopify. Queried ${shopifyLookup.queried_at}. The report uses the first value from the list metafield order.type.`
]];
summary.getRange("F29:J31").format = {
  fill: colors.lightGreen,
  wrapText: true,
  verticalAlignment: "top",
  borders: { preset: "all", style: "thin", color: colors.green },
};
summary.getRange("A:A").format.columnWidth = 24;
summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:F").format.columnWidth = 15;
summary.getRange("G:J").format.columnWidth = 16;
summary.getRange(`A1:J${Math.max(31, orderTypeEndRow)}`).format.wrapText = true;
summary.freezePanes.freezeRows(2);

// Status colors on action sheets.
queue.getRange(`B5:B${4 + excludeNow.length}`).format = { fill: colors.lightRed, font: { bold: true, color: colors.red } };
if (marginReview.length > 0) {
  const start = 5 + excludeNow.length;
  queue.getRange(`B${start}:B${queueEnd}`).format = { fill: colors.lightGreen, font: { bold: true, color: colors.green } };
}
exclude.getRange(`B5:B${excludeEnd}`).format = { fill: colors.lightRed, font: { bold: true, color: colors.red } };
margin.getRange(`B5:B${marginEnd}`).format = { fill: colors.lightGreen, font: { bold: true, color: colors.green } };

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const checks = {
  summary: await workbook.inspect({
    kind: "table",
    sheetId: "Summary",
    range: `A1:J${Math.max(31, orderTypeEndRow)}`,
    include: "values,formulas",
    tableMaxRows: Math.max(31, orderTypeEndRow),
    tableMaxCols: 10,
    maxChars: 16000,
  }),
  queue: await workbook.inspect({
    kind: "table",
    sheetId: "Action Queue",
    range: `A1:N${queueEnd}`,
    include: "values,formulas",
    tableMaxRows: 12,
    tableMaxCols: 14,
    maxChars: 12000,
  }),
  errors: await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "final formula error scan",
    maxChars: 8000,
  }),
};
console.log("SUMMARY_CHECK");
console.log(checks.summary.ndjson);
console.log("QUEUE_CHECK");
console.log(checks.queue.ndjson);
console.log("ERROR_CHECK");
console.log(checks.errors.ndjson);

const previewRanges = {
  "Summary": `A1:J${Math.max(31, orderTypeEndRow)}`,
  "Action Queue": `A1:N${Math.min(queueEnd, 24)}`,
  "Exclude Now": `A1:N${Math.min(excludeEnd, 24)}`,
  "Margin Review": `A1:N${marginEnd}`,
  "Source Data": "A1:U15",
};
for (const [sheetName, range] of Object.entries(previewRanges)) {
  const blob = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  const safe = sheetName.replaceAll(" ", "-").toLowerCase();
  await fs.writeFile(`${previewDir}/${safe}.png`, new Uint8Array(await blob.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({
  outputPath,
  previewDir,
  counts: {
    sourceProducts: records.length,
    excludeNow: excludeNow.length,
    performanceExclude: performanceExclude.length,
    zeroRoas: zeroRoas.length,
    zeroAdditional: zeroAdditional.length,
    marginReview: marginReview.length,
    actionQueue: actionQueue.length,
    shopifyCoverage,
  },
  totals,
  significantSpend,
}, null, 2));
