import urllib.request
import os
import re
import gzip
import time
import requests
from bs4 import BeautifulSoup
import argparse
import sys
import logging # Import logging
from datetime import datetime # Import datetime


# --- Configuration & Constants ---
# Set the file version
ver = '1.5:YYYY-MM-DD' # TODO: Update date when finalizing

# Define known data types based on observed structure
# TODO: Verify and potentially expand this list
KNOWN_DATA_TYPES = ['trading', 'spot', 'kline_for_metatrader4', 'premium_index', 'spot_index']

# Setup basic logging
# TODO: Make logging configurable (level, file output) via args
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Argument Validation Functions ---
def validate_date_format(date_string):
    """Validates that a string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return date_string
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_string}'. Please use YYYY-MM-DD.")

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Bybit Historical Data Downloader')
    parser.add_argument('--start-date', required=True, type=validate_date_format, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=validate_date_format, help='End date in YYYY-MM-DD format (optional)')
    parser.add_argument('--coins', required=True, help="Comma-separated list of coin pairs (e.g., BTCUSDT,ETHUSDT) or 'ALL'")
    parser.add_argument('--data-types', default='trading', help=f"Comma-separated list of data types (e.g., trading,spot) or 'ALL'. Default: trading. Known types: {', '.join(KNOWN_DATA_TYPES)}")
    parser.add_argument('--output-dir', default='./data', help='Directory to save downloaded data (default: ./data)')
    parser.add_argument('--base-url', default='https://public.bybit.com/', help='Base URL for Bybit public data (default: https://public.bybit.com/)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {ver}')
    # TODO: Add arguments for logging level, log file, etc.

    args = parser.parse_args()

    # --- Argument Validation/Processing ---
    # TODO: Add more robust handling for 'ALL' coins (discover available coins?)

    # Process coins
    if args.coins.upper() == 'ALL':
        logging.warning("'--coins ALL' is specified, but coin filtering is not yet fully implemented based on discovery. Will attempt to download all found coins for the specified types.")
        target_coins = ['ALL'] # Placeholder
    else:
        target_coins = [coin.strip().upper() for coin in args.coins.split(',')]

    # Process data types
    if args.data_types.upper() == 'ALL':
        target_data_types = KNOWN_DATA_TYPES
    else:
        target_data_types = [dt.strip().lower() for dt in args.data_types.split(',')]
        # Validate specified types against known types
        for dt in target_data_types:
            if dt not in KNOWN_DATA_TYPES:
                logging.error(f"Unknown data type '{dt}'. Please use one of {KNOWN_DATA_TYPES} or 'ALL'.")
                sys.exit(1) # Exit if unknown type is specified

    logging.info("--- Configuration ---")
    logging.info(f"Start Date: {args.start_date}")
    logging.info(f"End Date: {args.end_date if args.end_date else 'Not set'}")
    logging.info(f"Coins: {', '.join(target_coins)}")
    logging.info(f"Data Types: {', '.join(target_data_types)}")
    logging.info(f"Output Directory: {args.output_dir}")
    logging.info(f"Base URL: {args.base_url}")
    logging.info("---------------------")

    return args, target_coins, target_data_types

# Set the file version
ver = '1.3:02/05/23'

# Define the base URL
base_url = 'https://public.bybit.com/trading/'

# Select the start date
start_date = '2024-10-01'

# Set the list of coins
coins = ['BTCUSDT', 'ETHUSDT', 'XVGUSDT']

# Create a function to download the files
def download_file(url, local_path):
    with urllib.request.urlopen(url) as response, open(local_path, 'wb') as out_file:
        data = response.read()
        out_file.write(data)


# Create a function to check if a file exists
def file_exists(local_path):
    return os.path.exists(local_path)

def download_and_extract(csv_url, archive_path, extracted_path):
    """Downloads a gzipped CSV, extracts it, and removes the archive."""
    download_successful = False
    # Download the archive file if the extracted file doesn't exist
    if not file_exists(extracted_path):
        # Also check if archive exists (e.g., from interrupted previous run)
        if not file_exists(archive_path):
            try:
                logging.info(f'Downloading: {csv_url} to {archive_path}')
                # Use requests for consistency and better error handling
                response = requests.get(csv_url, stream=True)
                response.raise_for_status()
                with open(archive_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                time.sleep(0.1) # Be polite
                download_successful = True
            except requests.exceptions.RequestException as e:
                logging.error(f"Error downloading {csv_url}: {e}")
                # Attempt to clean up potentially corrupted file
                if file_exists(archive_path):
                    try:
                        os.remove(archive_path)
                    except OSError as oe:
                        logging.warning(f"Could not remove partially downloaded file {archive_path}: {oe}")
                return False # Indicate failure
            except Exception as e: # Catch other potential errors during download/write
                logging.error(f"An unexpected error occurred during download of {csv_url}: {e}")
                if file_exists(archive_path):
                    try: os.remove(archive_path)
                    except OSError as oe: pass # Ignore cleanup error
                return False
        else:
             logging.info(f"Archive file {archive_path} already exists. Proceeding to extraction.")
             download_successful = True # Archive exists, ready for extraction attempt

    # Extract the gzip archive if download was successful (or archive already existed)
    # and extracted file doesn't exist yet
    if download_successful and not file_exists(extracted_path):
        try:
            logging.info(f'Extracting: {archive_path} to {extracted_path}')
            with gzip.open(archive_path, 'rb') as f_in:
                with open(extracted_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            # Remove the archive file after successful extraction
            try:
                os.remove(archive_path)
                # logging.info(f'Removed archive: {archive_path}') # A bit verbose
            except OSError as e:
                logging.warning(f"Could not remove archive file {archive_path}: {e}")
            return True # Indicate success
        except gzip.BadGzipFile:
            logging.error(f"Bad Gzip file {archive_path}. It might be corrupted or not a gzip file.")
            # Optionally remove bad archive: os.remove(archive_path)
            return False # Indicate failure
        except Exception as e:
            logging.error(f"Error extracting {archive_path}: {e}")
            return False # Indicate failure
    elif file_exists(extracted_path):
         logging.info(f"Skipping download/extraction - extracted file {extracted_path} already exists.")
         return True # Already exists counts as success for this file
    else:
         # Download failed in the block above, message already logged
         return False # Indicate failure

# --- File Processing Logic ---
def process_directory(current_url, current_output_path, data_type_name, args, target_coins):
    """Recursively processes a directory, downloading and extracting relevant files."""
    logging.info(f"Processing directory: {current_url}")
    try:
        response = requests.get(current_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching directory URL {current_url}: {e}")
        return 0, 0 # Stop processing this branch if listing fails

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')

    files_processed_count = 0
    files_skipped_count = 0
    subdirs_processed = []

    # --- Process Files (.csv.gz) at Current Level ---
    csv_links = [link for link in links if link.get('href') and link.get('href').lower().endswith('.csv.gz')]
    if csv_links:
        logging.info(f"Found {len(csv_links)} potential .csv.gz files in {current_url}.")
        # Берем первые 3 файла для анализа формата имени
        sample_files = [csv_link.text for csv_link in csv_links[:3]]
        logging.info(f"Sample filenames: {', '.join(sample_files)}")
        
        for csv_link in csv_links:
            csv_name = csv_link.text
            # --- Extract Date ---
            # TODO: Improve robustness for different formats (e.g., monthly: YYYY-MM)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', csv_name)
            if not date_match:
                # Attempt to find year-month if daily fails (basic pattern)
                date_match_monthly = re.search(r'(\d{4}-\d{2})', csv_name)
                if date_match_monthly:
                    # For monthly files, treat as the first day for filtering purposes
                    csv_date = date_match_monthly.group(1) + '-01'
                    logging.debug(f"Extracted monthly date {date_match_monthly.group(1)} from '{csv_name}', using {csv_date} for filtering.")
                else:
                    logging.warning(f"Could not extract recognizable date (YYYY-MM-DD or YYYY-MM) from '{csv_name}'. Skipping.")
                    files_skipped_count += 1
                    continue
            else:
                csv_date = date_match.group(1)

            # --- Date Filtering ---
            if csv_date < args.start_date:
                logging.info(f"Skipping {csv_name} - date {csv_date} is before start date {args.start_date}")
                files_skipped_count += 1
                continue
            if args.end_date and csv_date > args.end_date:
                # We need to be careful with monthly files and end_date.
                # If end_date is 2023-05-15, we should still potentially include 2023-05 monthly file.
                # Let's refine this: Only skip if the file's *start* date (csv_date) is strictly *after* the end_date.
                if csv_date > args.end_date:
                     logging.info(f"Skipping {csv_name} - date {csv_date} is after end date {args.end_date}")
                     files_skipped_count += 1
                     continue

            # --- Coin Filtering (Basic - from filename) ---
            # TODO: Enhance coin extraction and filtering based on path components as well.
            # This basic check assumes coin is at the start or follows a pattern.
            file_coin = None
            # Улучшенные паттерны определения имени монеты
            # Для файлов в формате BTCUSDT2023-12-31.csv.gz
            match_coin = re.match(r'^([A-Z0-9]+)(?=\d{4}-\d{2}-\d{2})', csv_name)
            if match_coin:
                file_coin = match_coin.group(1)
            else:
                # Попробуем извлечь название монеты из пути для случая, когда файл находится в папке монеты
                # Например, в структуре: /trading/BTCUSDT/...
                coin_from_path = os.path.basename(os.path.dirname(current_url.rstrip('/')))
                if coin_from_path and coin_from_path.upper() != 'TRADING' and coin_from_path.upper() != 'SPOT':
                    file_coin = coin_from_path.upper()
                    logging.info(f"Using coin name from path: {file_coin} for file {csv_name}")

            if file_coin and 'ALL' not in target_coins and file_coin not in target_coins:
                logging.info(f"Skipping {csv_name} - coin {file_coin} (from filename) not in target list.")
                files_skipped_count += 1
                continue
            elif not file_coin:
                logging.debug(f"Could not reliably determine coin from filename '{csv_name}'. Proceeding without filename-based coin filtering.")

            # --- File Handling ---
            csv_url = f"{current_url.rstrip('/')}/{csv_link.get('href')}"
            extracted_filename = csv_name[:-3] # Remove .gz
            # Ensure the output path exists (it should normally, but safety first)
            os.makedirs(current_output_path, exist_ok=True)
            extracted_path = os.path.join(current_output_path, extracted_filename)
            archive_path = os.path.join(current_output_path, csv_name)

            logging.info(f"Downloading file: {csv_name}, date: {csv_date}")
            if download_and_extract(csv_url, archive_path, extracted_path):
                files_processed_count += 1
                logging.info(f"Successfully processed file: {csv_name}")
            else:
                 files_skipped_count += 1 # Failed download/extract
                 logging.warning(f"Failed to download or extract file: {csv_name}")

    # --- Process Subdirectories (Recursion) ---
    subdir_links = [link for link in links if link.get('href') and link.get('href').endswith('/') and link.get('href') != '../']
    if subdir_links:
        logging.debug(f"Found {len(subdir_links)} subdirectories in {current_url}.")
        for subdir_link in subdir_links:
            subdir_name = subdir_link.get('href')[:-1] # Remove trailing slash
            next_url = f"{current_url.rstrip('/')}/{subdir_link.get('href')}"
            next_output_path = os.path.join(current_output_path, subdir_name)

            # --- Heuristic for Subdirectory Type --- #
            # TODO: Make this logic more robust, potentially data_type specific config
            is_coin_dir = False
            looks_like_year = bool(re.fullmatch(r'\d{4}', subdir_name))

            # Simple check: If the subdir name matches a pattern of typical coin pairs (e.g., uppercase letters + USDT/USD/BTC etc.)
            # and we are in specific data_type dirs known to have coin subdirs.
            if data_type_name in ['spot', 'kline_for_metatrader4', 'premium_index', 'spot_index'] and re.fullmatch(r'[A-Z0-9]+', subdir_name):
                 is_coin_dir = True
                 logging.debug(f"Directory '{subdir_name}' looks like a coin directory for data type '{data_type_name}'.")

            # --- Filtering & Recursion Decision ---
            should_recurse = True
            if is_coin_dir:
                coin_name_from_dir = subdir_name.upper()
                if 'ALL' not in target_coins and coin_name_from_dir not in target_coins:
                    logging.info(f"Skipping directory {subdir_name} - coin not in target list: {target_coins}")
                    should_recurse = False

            # Add year filtering later if needed
            # if looks_like_year:
            #    # Compare year from subdir_name with start/end date args

            if should_recurse:
                # Ensure output directory for the next level exists BEFORE recursing
                os.makedirs(next_output_path, exist_ok=True)
                subdir_files_processed, subdir_files_skipped = process_directory(next_url, next_output_path, data_type_name, args, target_coins)
                files_processed_count += subdir_files_processed
                files_skipped_count += subdir_files_skipped
                subdirs_processed.append(subdir_name)
            else:
                 files_skipped_count += 1 # Count skipped directory as one skip for summary

    log_suffix = f" files processed: {files_processed_count}, files skipped/errors: {files_skipped_count}"
    if subdirs_processed:
        log_suffix += f", subdirs processed: {len(subdirs_processed)} ({', '.join(subdirs_processed[:3])}{'...' if len(subdirs_processed)>3 else ''})"

    logging.info(f"Finished processing {current_url}. Totals for this level and below ->{log_suffix}")
    return files_processed_count, files_skipped_count # Return counts for aggregation

# --- Main Download Logic ---
def main():
    args, target_coins, target_data_types = parse_arguments()

    # Create the main output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Initial Request to List Data Types ---
    logging.info(f"Fetching available data types from {args.base_url}...")
    try:
        response = requests.get(args.base_url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching base URL {args.base_url}: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')

    # --- Loop Through Data Types ---
    available_data_types_on_server = []
    for link in links:
        href = link.get('href')
        if href and href.endswith('/') and href != '../':
            available_data_types_on_server.append(href[:-1])

    logging.info(f"Found data type directories on server: {', '.join(available_data_types_on_server)}")

    for data_type_name in target_data_types:
        if data_type_name not in available_data_types_on_server:
             logging.warning(f"Requested data type '{data_type_name}' not found directly under {args.base_url}. Skipping.")
             continue

        logging.info(f"\n--- Processing Data Type: {data_type_name} ---")

        # Create the subdirectory for this data type
        data_type_dir = os.path.join(args.output_dir, data_type_name)
        os.makedirs(data_type_dir, exist_ok=True)

        # Если это не ALL, напрямую переходим к запрошенным монетам, а не сканируем все
        if 'ALL' not in target_coins:
            total_processed = 0
            total_skipped = 0
            
            for coin in target_coins:
                logging.info(f"Directly accessing coin: {coin} for data type: {data_type_name}")
                # Конструируем URL для конкретной монеты
                coin_url = f"{args.base_url.rstrip('/')}/{data_type_name}/{coin}/"
                coin_dir = os.path.join(data_type_dir, coin)
                os.makedirs(coin_dir, exist_ok=True)
                
                try:
                    # Сначала проверяем, существует ли эта монета на сервере
                    response = requests.head(coin_url)
                    if response.status_code == 200:
                        # Если монета существует, обрабатываем её
                        coin_processed, coin_skipped = process_directory(coin_url, coin_dir, data_type_name, args, target_coins)
                        total_processed += coin_processed
                        total_skipped += coin_skipped
                    else:
                        logging.warning(f"Coin {coin} not found for data type {data_type_name} (URL: {coin_url})")
                        total_skipped += 1
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error checking coin URL {coin_url}: {e}")
                    total_skipped += 1
            
            logging.info(f"--- Finished processing data type: {data_type_name}. Total files processed/verified: {total_processed}, total skipped/errors: {total_skipped} ---")
        else:
            # Если запрошены все монеты, используем существующую логику сканирования директории
            dir_url = f"{args.base_url.rstrip('/')}/{data_type_name}/" # Ensure trailing slash
            total_processed, total_skipped = process_directory(dir_url, data_type_dir, data_type_name, args, target_coins)
            logging.info(f"--- Finished processing data type: {data_type_name}. Total files processed/verified: {total_processed}, total skipped/errors: {total_skipped} ---")


# Wrap the script execution in a main function call
if __name__ == "__main__":
    main()
