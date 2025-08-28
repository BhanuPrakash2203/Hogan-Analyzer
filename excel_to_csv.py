import pandas as pd
import sys
import os
import logging
from datetime import datetime

def setup_logging(log_file_path):
    """Set up logging to specified file and console"""
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, mode='a'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

def find_excel_file(folder_path):
    """Find first Excel file in the given folder"""
    for file in os.listdir(folder_path):
        if file.lower().endswith(('.xlsx', '.xls')):
            return os.path.join(folder_path, file)
    return None

def create_combined_links_data(output_folder, logger):
    """Create the combined linksData.csv file with proper mapping"""
    try:
        link_df = pd.read_csv(os.path.join(output_folder, 'activity_program_mapping.csv'))
        sql_df = pd.read_csv(os.path.join(output_folder, 'sql_program_mapping.csv'))
        
        link_data = link_df[['ACTIVITY', 'TYPE', 'PGMID']].copy()
        link_data['TYPE'] = 'HOGAN Link Activity'
        
        sql_data = sql_df[['ACTIVITY', 'TYPE']].copy()
        sql_data['PGMID'] = sql_df['SOURCE']
        sql_data['TYPE'] = 'HOGAN SQL Activity'
        
        combined_df = pd.concat([link_data, sql_data], ignore_index=True)
        
        if not all(col in combined_df.columns for col in ['ACTIVITY', 'TYPE', 'PGMID']):
            logger.error("Combined dataframe missing required columns")
            return False
            
        output_file = os.path.join(output_folder, 'linksData.csv')
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Created combined output {output_file} with {len(combined_df)} records")
        logger.info("\nSample of combined data:")
        logger.info(combined_df.head().to_string())
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create combined links data: {str(e)}", exc_info=True)
        return False

def extract_transaction_data(excel_file, output_folder, logger):
    """Append transaction data to activities.csv and linksData.csv"""
    try:
        all_sheets = pd.read_excel(excel_file, sheet_name=None)

        matched_sheet = None
        for name, sheet in all_sheets.items():
            columns = [col.strip() for col in sheet.columns]
            if set(['Application', 'Function']).issubset(columns):
                if any('Type' in col for col in columns) and 'PGM' in columns and 'DESCR' in columns:
                    matched_sheet = sheet
                    break

        if matched_sheet is None:
            logger.warning("No suitable sheet found for transaction extraction.")
            return

        df = matched_sheet.copy()
        type_col = next(col for col in df.columns if 'Type' in col)

        df = df[['Application', 'Function', type_col, 'PGM', 'DESCR']].copy()
        df['Application'] = df['Application'].astype(str).str.strip()
        df['Function'] = df['Function'].astype(str).str.strip()
        df[type_col] = df[type_col].astype(str).str.strip()
        df['PGM'] = df['PGM'].astype(str).str.strip()
        df['DESCR'] = df['DESCR'].astype(str).str.strip()

        df['ACTIVITY'] = df['Application'] + '-' + df['Function'] + '-' + df[type_col]
        df['TYPE'] = 'TRAN'
        df['SOURCE'] = df['PGM']
        df['DESCR.'] = df['DESCR']

        # Append to activities.csv
        transaction_df = df[['ACTIVITY', 'TYPE', 'SOURCE', 'DESCR.']]
        activities_path = os.path.join(output_folder, 'activities.csv')
        if os.path.exists(activities_path):
            existing_df = pd.read_csv(activities_path)
            combined_df = pd.concat([existing_df, transaction_df], ignore_index=True)
        else:
            combined_df = transaction_df

        combined_df.to_csv(activities_path, index=False)
        logger.info(f"Appended {len(transaction_df)} transaction records to {activities_path} (new total: {len(combined_df)})")

        # Create unique_activities.csv with only ACTIVITY, TYPE, DESCR. columns
        unique_df = combined_df[['ACTIVITY', 'TYPE', 'DESCR.']].drop_duplicates()
        unique_path = os.path.join(output_folder, 'unique_activities.csv')
        unique_df.to_csv(unique_path, index=False)
        logger.info(f"Created {unique_path} with {len(unique_df)} unique rows")


        # Append to linksData.csv
        links_path = os.path.join(output_folder, 'linksData.csv')
        transaction_links_df = df[['ACTIVITY', 'PGM']].copy()
        transaction_links_df.rename(columns={'PGM': 'PGMID'}, inplace=True)
        transaction_links_df['TYPE'] = 'Hogan Transaction'
        transaction_links_df = transaction_links_df[['ACTIVITY', 'TYPE', 'PGMID']]

        if os.path.exists(links_path):
            existing_links_df = pd.read_csv(links_path)
            links_combined_df = pd.concat([existing_links_df, transaction_links_df], ignore_index=True)
        else:
            links_combined_df = transaction_links_df

        links_combined_df.to_csv(links_path, index=False)
        logger.info(f"Appended {len(transaction_links_df)} Hogan Transaction records to {links_path} (new total: {len(links_combined_df)})")

    except Exception as e:
        logger.error(f"Failed to extract and merge transaction data: {str(e)}", exc_info=True)



def process_excel_to_csv(input_folder, output_folder, log_file_path):
    logger = setup_logging(log_file_path)
    
    try:
        logger.info(f"Starting processing with:\n"
                   f"- Input folder: {input_folder}\n"
                   f"- Output folder: {output_folder}\n"
                   f"- Log file: {log_file_path}")
        
        excel_file = find_excel_file(input_folder)
        if not excel_file:
            logger.error(f"No Excel file found in input folder {input_folder}")
            return False
        
        logger.info(f"Found Excel file: {excel_file}")
        
        os.makedirs(output_folder, exist_ok=True)
        
        sheet1 = pd.read_excel(excel_file, sheet_name=0)
        sheet2 = pd.read_excel(excel_file, sheet_name=1)
        
        required_cols_sheet1 = ['ACTIVITY', 'TYPE', 'SOURCE', 'DESCR.']
        if not all(col in sheet1.columns for col in required_cols_sheet1):
            missing = set(required_cols_sheet1) - set(sheet1.columns)
            logger.error(f"First sheet missing columns: {missing}")
            return False
        
        df1 = sheet1[required_cols_sheet1].copy()
        output_file1 = os.path.join(output_folder, 'activities.csv')
        df1.to_csv(output_file1, index=False)
        logger.info(f"Created {output_file1} with {len(df1)} records")
        
        required_cols_sheet2 = ['PGM LINK', 'PGM ID', 'DESCR']
        col_mapping = {
            'PGM LINK': ['PGM LINK', 'LINK'],
            'PGM ID': ['PGM ID', 'ID'],
            'DESCR': ['DESCR', 'DESCRIPTION', 'DESC']
        }
        
        found_cols = {}
        for target_col, possible_names in col_mapping.items():
            for name in possible_names:
                if name in sheet2.columns:
                    found_cols[target_col] = name
                    break
            else:
                logger.error(f"Could not find column matching {target_col} in second sheet")
                return False
        
        df2 = sheet2[list(found_cols.values())].copy()
        df2.columns = required_cols_sheet2
        
        df2['PGM LINK'] = df2['PGM LINK'].astype(str).str.strip()
        df2['PGM ID'] = df2['PGM ID'].astype(str).str.strip()
        
        output_file2 = os.path.join(output_folder, 'programs.csv')
        df2.to_csv(output_file2, index=False)
        logger.info(f"Created {output_file2} with {len(df2)} records")
        
        df_link = df1[df1['TYPE'].str.strip().str.upper() == 'LINK'].copy()
        df_link['SOURCE'] = df_link['SOURCE'].astype(str).str.strip()
        logger.info(f"Found {len(df_link)} LINK activities")
        
        pgm_mapping = df2.set_index('PGM LINK')['PGM ID'].to_dict()
        df_link['PGMID'] = df_link['SOURCE'].map(pgm_mapping)
        
        output_file3 = os.path.join(output_folder, 'activity_program_mapping.csv')
        df_link[['ACTIVITY', 'TYPE', 'SOURCE', 'PGMID']].to_csv(output_file3, index=False)
        logger.info(f"Created {output_file3} with {len(df_link)} records")
        
        df_sql = df1[df1['TYPE'].str.strip().str.upper() == 'SQL'].copy()
        df_sql['SOURCE'] = df_sql['SOURCE'].astype(str).str.strip()
        logger.info(f"Found {len(df_sql)} SQL activities")
        
        output_file4 = os.path.join(output_folder, 'sql_program_mapping.csv')
        df_sql[['ACTIVITY', 'TYPE', 'SOURCE', 'DESCR.']].to_csv(output_file4, index=False)
        logger.info(f"Created {output_file4} with {len(df_sql)} records")
        
        if not create_combined_links_data(output_folder, logger):
            return False

        # Step 5: Extract transaction data
        extract_transaction_data(excel_file, output_folder, logger)
        
        matched_count = df_link['PGMID'].notna().sum()
        logger.info("\nSUMMARY:")
        logger.info(f"LINK activities: {len(df_link)} (Matched: {matched_count}, Unmatched: {len(df_link)-matched_count})")
        logger.info(f"SQL activities: {len(df_sql)}")
        logger.info("Processing completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {os.path.basename(__file__)} <input_folder> <output_folder> <log_file_path>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    log_file_path = sys.argv[3]
    
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder {input_folder} not found")
        sys.exit(1)
    
    success = process_excel_to_csv(input_folder, output_folder, log_file_path)
    sys.exit(0 if success else 1)
