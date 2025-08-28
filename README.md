# Hogan CSV Analyzer for CAST

This repository provides a **Custom CAST Analyzer** for processing **Hogan CSV files**. The analyzer reads Hogan activity definitions from CSV files and creates **CAST Custom Objects** that represent different Hogan activities (LINK, SQL, HDB, etc.).

---

## ðŸ“Œ Overview

The analyzer is implemented as a CAST UA (Universal Analyzer) **Extension** in Python. It:

- Reads and parses Hogan CSV files (comma-delimited).
- Identifies specific Hogan activity types (LINK, SQL, HDB, etc.).
- Creates **Custom Objects** in CAST with appropriate types.
- Associates metadata such as descriptions and bookmarks.
- Establishes links from the source file to the created objects.

---

## âš™ï¸ How It Works

### File Processing
- The analyzer triggers on any file ending with **`.csv`**.
- It attempts to read the file using multiple encodings (`utf-8-sig`, `latin-1`, `iso-8859-1`, `cp1252`) for compatibility.
- Uses Pythonâ€™s `csv.DictReader` to parse rows.

### Required Columns
- The analyzer expects at least two columns in the CSV file:
  - `ACTIVITY`
  - `TYPE`
- An optional column `DESCR.` is used for descriptions.

### Supported Activity Types
The analyzer maps Hogan activity types to CAST custom objects:

| CSV `TYPE` Value | Custom Object Type |
|------------------|---------------------|
| `LINK`           | `HOGAN_Link_Activity` |
| `SQL`            | `HOGAN_SQL_Activity` |
| `HDB`            | `Hogan_Hierarchical_Database_Activity` |
| `DC`, `DC-T`     | `Hogan_Data_Communications_Activity` |
| `SDB`            | `Hogan_Sequential_Database_Activity` |
| `SORT`           | `Hogan_Sort_Activity` |
| `TRAN`           | `Hogan_Transaction` |

### Object Creation
- A **CustomObject** is created for each recognized activity.
- Each object has:
  - **GUID**: generated based on activity name and row number.
  - **Name**: value from `ACTIVITY` column.
  - **Type**: mapped from `TYPE` column.
  - **Parent**: source CSV file.
  - **Description**: stored if available from `DESCR.` column.
  - **Bookmark**: links back to the exact row in the CSV file.

### Links
- A `callLink` is created between the source file and the newly created Hogan object.

### Logging
- Logs progress and warnings during execution.
- Reports how many LINK and SQL activities were processed from each file.

---

## ðŸ“‚ Code Structure

```plaintext
HoganCSVAnalyzer
 â”œâ”€â”€ start_file()          â†’ Entry point for processing .csv files
 â”œâ”€â”€ process_hogan_csv()   â†’ Reads CSV, iterates rows, creates objects
 â”œâ”€â”€ create_hogan_object() â†’ Creates and saves CAST Custom Objects
 â”œâ”€â”€ generate_guid()       â†’ Creates unique identifiers for objects
```

---

## ðŸš€ Usage
1. Place your Hogan activity CSV files in the CAST analysis source folder.
2. Register the analyzer as a CAST UA extension.
3. Run the CAST analysis â€” the extension will:
   - Parse `.csv` files.
   - Create Hogan activity objects.
   - Establish links and store descriptions.

---

## ðŸ” Example
### Sample CSV Input
```csv
ACTIVITY,TYPE,DESCR.
Customer_Link,LINK,Customer to Order link
Order_Query,SQL,Fetch orders by customer
Main_Transaction,TRAN,Main transaction handler
```

### Result in CAST
- **HOGAN_Link_Activity** named `Customer_Link`
- **HOGAN_SQL_Activity** named `Order_Query`
- **Hogan_Transaction** named `Main_Transaction`
- Each linked to the CSV file and bookmark.

---

## âš ï¸ Error Handling
- If required columns are missing â†’ logs a warning, skips file.
- If row has issues â†’ logs a warning, continues with next row.
- If encoding fails â†’ tries next encoding until success or final failure.

---

## âœ¨ Key Benefits
- Automates **Hogan activity modeling** from CSV to CAST.
- Supports multiple Hogan activity types.
- Provides traceability via bookmarks and file links.
- Flexible CSV encoding support.

---

## ðŸ“œ Author
Developed by **BBA**
