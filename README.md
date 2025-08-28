# Hogan CSV Analyzer for CAST

This repository provides a **Custom CAST Analyzer** for processing **Hogan CSV files**. The analyzer reads Hogan activity definitions from CSV files and creates **CAST Custom Objects** that represent different Hogan activities (LINK, SQL, HDB, etc.).

---

## Overview

The analyzer is implemented as a CAST UA (Universal Analyzer) **Extension** in Python. It:

- Reads and parses Hogan CSV files (comma-delimited).
- Identifies specific Hogan activity types (LINK, SQL, HDB, etc.).
- Creates **Custom Objects** in CAST with appropriate types.
- Associates metadata such as descriptions and bookmarks.
- Establishes links from the source file to the created objects.

---

## How It Works

### File Processing
- The analyzer triggers on any file ending with **`.csv`**.
- It attempts to read the file using multiple encodings (`utf-8-sig`, `latin-1`, `iso-8859-1`, `cp1252`) for compatibility.
- Uses Python’s `csv.DictReader` to parse rows.

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

## Code Structure

```plaintext
HoganCSVAnalyzer
 ├── start_file()          → Entry point for processing .csv files
 ├── process_hogan_csv()   → Reads CSV, iterates rows, creates objects
 ├── create_hogan_object() → Creates and saves CAST Custom Objects
 ├── generate_guid()       → Creates unique identifiers for objects
