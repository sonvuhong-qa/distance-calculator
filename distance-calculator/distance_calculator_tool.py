import argparse
import logging
import os
import re
import sys
import time
import traceback
from datetime import datetime
from multiprocessing import Process
from urllib.parse import quote

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging (will be configured in __init__)
logger = logging.getLogger(__name__)


class GoogleMapsDistanceCalculator:
    def __init__(self, csv_file_path, company_address, start_row=0, end_row=None, debug_mode=False, worker_id=0, headless=False):
        self.csv_file = csv_file_path
        self.company_address = company_address
        self.driver = None
        self.start_row = start_row
        self.end_row = end_row  # None means process to end of file
        self.wait = None
        self.debug_mode = debug_mode
        self.worker_id = worker_id  # 0 for single mode, 1+ for parallel workers
        self.headless = headless
        self.debug_folder = "debug_screenshots"

        # Setup logging
        self._setup_logging()

        # Create debug folder if in debug mode
        if self.debug_mode:
            os.makedirs(self.debug_folder, exist_ok=True)
            logger.info(f"Debug mode enabled. Artifacts will be saved to {self.debug_folder}/")

    def _setup_logging(self):
        """Configure logging with appropriate level"""
        log_level = logging.DEBUG if self.debug_mode else logging.INFO

        # Clear existing handlers
        logger.handlers.clear()
        logger.setLevel(log_level)

        # Worker-specific prefix for log files
        worker_prefix = f"worker_{self.worker_id}_" if self.worker_id > 0 else ""

        # Console handler (only for worker 0 or single mode to avoid clutter)
        if self.worker_id == 0:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # File handler for normal logs
        log_filename = f'{worker_prefix}distance_calculator.log'
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Debug file handler if in debug mode
        if self.debug_mode:
            debug_filename = f'{worker_prefix}distance_calculator_debug.log'
            debug_handler = logging.FileHandler(debug_filename)
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(file_formatter)
            logger.addHandler(debug_handler)

    def setup_driver(self):
        """Setup Chrome driver with automatic driver management"""
        try:
            # Check if running in Google Colab
            is_colab = False
            try:
                import google.colab
                is_colab = True
            except ImportError:
                pass

            options = webdriver.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument("--disable-extensions")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Additional stability options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-gpu-sandbox')
            options.add_argument('--remote-debugging-port=0')  # Avoid port conflicts

            # Add realistic User-Agent to appear as normal browser
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Headless mode configuration
            if self.headless or is_colab:
                options.add_argument('--headless=new')  # New headless mode (Chrome 109+)
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')  # Set window size in headless
                if is_colab:
                    logger.info(f"Worker {self.worker_id}: Detected Google Colab environment. Forcing headless mode.")
                else:
                    logger.info(f"Worker {self.worker_id}: Running in headless mode")

            if is_colab:
                # In Colab, we use the pre-installed chromium-browser and chromedriver
                # if available, otherwise fallback to ChromeDriverManager
                try:
                    self.driver = webdriver.Chrome(options=options)
                except Exception:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
            else:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)

            # Execute CDP command to mask webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            # Only maximize if not headless
            if not self.headless:
                self.driver.maximize_window()

            # Navigate to Google first to establish cookies, then to Maps
            self.driver.get('https://www.google.com')
            time.sleep(1)

            self.wait = WebDriverWait(self.driver, 15)
            logger.info(f"Worker {self.worker_id}: Browser setup successful")
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Failed to setup browser: {e}")
            if self.debug_mode:
                logger.debug(traceback.format_exc())
            raise

    def save_debug_artifacts(self, employee_id, status="failed", distance=None):
        """Save screenshot and page source for debugging"""
        if not self.debug_mode:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = f"{self.debug_folder}/{employee_id}_{timestamp}_{status}"

        try:
            # Save screenshot
            screenshot_path = f"{prefix}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.debug(f"Screenshot saved: {screenshot_path}")

            # Save page source
            html_path = f"{prefix}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.debug(f"Page source saved: {html_path}")

            if distance:
                logger.debug(f"Distance found: {distance} km")

        except Exception as e:
            logger.warning(f"Failed to save debug artifacts: {e}")

    def get_expanded_selectors(self):
        """Return expanded list of selectors for distance extraction"""
        return [
            # XPath selectors
            ('xpath', '//div[@id="section-directions-trip-0"]//div[contains(@class, "Fk3sm")]//div[contains(text(), "km")]'),
            ('xpath', '//div[contains(@jstcache, "")]//div[contains(text(), "km")]'),
            ('xpath', '//span[contains(@class, "fontBodyMedium")]//span[contains(text(), "km")]'),
            ('xpath', '//div[@class="XdKEzd"]//span[contains(text(), "km")]'),
            ('xpath', '//div[contains(@id, "section-directions-trip")]//span[contains(text(), "km")]'),
            ('xpath', '//div[@role="gridcell"]//span[contains(text(), "km")]'),
            ('xpath', '//div[contains(@class, "directions-info")]//span[contains(text(), "km")]'),
            ('xpath', '//*[contains(text(), "km") and not(contains(text(), "km/h"))]'),

            # CSS selectors
            ('css', 'div.Fk3sm div'),
            ('css', 'div[jstcache] div'),
            ('css', 'span.fontBodyMedium span'),
            ('css', 'div.XdKEzd span'),
            ('css', 'div[id*="section-directions"] span'),

            # Miles fallback (will convert to km)
            ('xpath', '//span[contains(text(), "mi") and not(contains(text(), "min"))]'),
            ('xpath', '//div[contains(text(), "mi") and not(contains(text(), "min"))]'),
        ]

    def get_distance_from_maps(self, employee_address, employee_id=None, retry_count=3):
        """Get distance with retry mechanism and comprehensive error handling"""
        for attempt in range(retry_count):
            error_type = None
            try:
                logger.debug(f"Attempt {attempt + 1}/{retry_count} for address: {employee_address}")

                # Build URL with encoded addresses (much more reliable than input fields)
                origin_encoded = quote(employee_address, safe='')
                dest_encoded = quote(self.company_address, safe='')
                maps_url = f'https://www.google.com/maps/dir/{origin_encoded}/{dest_encoded}/'

                logger.debug(f"Navigating to: {maps_url}")
                self.driver.get(maps_url)
                logger.debug("Navigated to Google Maps with pre-built URL")

                # Wait for route to calculate - use dynamic wait
                logger.debug("Waiting for route calculation...")
                try:
                    # Wait for any distance element to appear
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: any(
                            len(driver.find_elements(By.XPATH, f'//*[contains(text(), "{unit}")]')) > 0
                            for unit in ['km', 'mi']
                        )
                    )
                    logger.debug("Route calculation completed")
                except TimeoutException:
                    logger.warning("Timeout waiting for route calculation")
                    error_type = "ROUTE_TIMEOUT"

                # Additional wait for page to stabilize
                time.sleep(2)

                # Take debug screenshot before extraction
                if self.debug_mode and employee_id:
                    self.save_debug_artifacts(employee_id, status="before_extraction")

                # Extract distance using multiple methods
                distance = self.extract_distance()

                if distance:
                    logger.debug(f"✓ Successfully extracted distance: {distance} km")
                    if self.debug_mode and employee_id:
                        self.save_debug_artifacts(employee_id, status="success", distance=distance)
                    return distance
                else:
                    error_type = "EXTRACTION_FAILED"
                    logger.warning("Distance extraction returned None")

            except TimeoutException as e:
                error_type = error_type or "TIMEOUT"
                logger.warning(f"Timeout on attempt {attempt + 1} for {employee_address}: {e}")
                if self.debug_mode:
                    logger.debug(traceback.format_exc())

            except Exception as e:
                error_type = error_type or "UNKNOWN"
                logger.error(f"Error on attempt {attempt + 1} ({error_type}): {e}")
                if self.debug_mode:
                    logger.debug(traceback.format_exc())

            # Save debug artifacts on failure
            if self.debug_mode and employee_id:
                self.save_debug_artifacts(employee_id, status=f"failed_{error_type}_attempt{attempt+1}")

            # Exponential backoff for retries
            if attempt < retry_count - 1:
                wait_time = 3 * (attempt + 1)  # 3, 6, 9 seconds
                logger.debug(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        logger.error(f"Failed to get distance after {retry_count} attempts")
        return None

    def extract_distance(self):
        """Extract distance from various possible elements with comprehensive logging"""
        logger.debug("Starting distance extraction...")
        selectors = self.get_expanded_selectors()

        for idx, (selector_type, selector) in enumerate(selectors, 1):
            try:
                logger.debug(f"Trying selector {idx}/{len(selectors)} ({selector_type}): {selector[:80]}...")

                if selector_type == 'xpath':
                    elements = self.driver.find_elements(By.XPATH, selector)
                elif selector_type == 'css':
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    continue

                logger.debug(f"  Found {len(elements)} elements")

                for elem_idx, element in enumerate(elements):
                    try:
                        text = element.text.strip()
                        if text:
                            logger.debug(f"  Element {elem_idx + 1} text: '{text}'")

                            # Try to extract km distance
                            match = re.search(r'([\d,\.]+)\s*km', text, re.IGNORECASE)
                            if match:
                                distance_str = match.group(1).replace(',', '.')
                                distance = float(distance_str)
                                logger.info(f"✓ Distance extracted: {distance} km using selector {idx}")
                                return distance

                            # Try to extract miles and convert
                            match = re.search(r'([\d,\.]+)\s*mi', text, re.IGNORECASE)
                            if match and 'min' not in text.lower():
                                distance_str = match.group(1).replace(',', '.')
                                miles = float(distance_str)
                                distance = miles * 1.60934  # Convert to km
                                logger.info(f"✓ Distance extracted: {distance:.2f} km (converted from {miles} mi) using selector {idx}")
                                return distance
                    except Exception as e:
                        logger.debug(f"  Error processing element {elem_idx + 1}: {e}")
                        continue

            except Exception as e:
                logger.debug(f"  Selector {idx} failed: {e}")
                if self.debug_mode:
                    logger.debug(traceback.format_exc())
                continue

        logger.warning("No distance found with any selector")
        return None

    def process_csv_batch(self, batch_size=50, specific_rows=None):
        """
        Process CSV in batches with resume capability.

        Args:
            batch_size: Number of rows to process before saving progress
            specific_rows: List of specific row indices to process (for retry mode).
                          If None, processes all rows in the start_row to end_row range.
        """
        df = pd.read_csv(self.csv_file, delimiter=';', encoding='utf-8-sig')

        if 'Distance_km' not in df.columns:
            df['Distance_km'] = None
        if 'Processing_Status' not in df.columns:
            df['Processing_Status'] = 'Pending'

        self.setup_driver()

        # Determine which rows to process
        if specific_rows is not None:
            # Retry mode: process only specific rows
            rows_to_process = specific_rows
            logger.info(f"Worker {self.worker_id}: Processing {len(rows_to_process)} specific rows (retry mode)")
        else:
            # Normal mode: process range
            total_rows = len(df)
            end_row = self.end_row if self.end_row is not None else total_rows
            end_row = min(end_row, total_rows)
            rows_to_process = list(range(self.start_row, end_row))
            logger.info(f"Worker {self.worker_id}: Processing rows {self.start_row} to {end_row-1} (total: {end_row - self.start_row} rows)")

        processed = 0
        failed_addresses = []

        for idx, index in enumerate(rows_to_process):
            row = df.iloc[index]

            # Skip if already processed (unless in retry mode with specific rows)
            if specific_rows is None and row['Processing_Status'] == 'Complete':
                continue

            address = row['Residence address']
            employee_id = row['ID']

            if specific_rows is not None:
                logger.info(f"Worker {self.worker_id}: Processing {idx + 1}/{len(rows_to_process)} - Row {index} - ID: {employee_id}")
            else:
                logger.info(f"Worker {self.worker_id}: Processing {index + 1}/{end_row} - ID: {employee_id}")

            distance = self.get_distance_from_maps(address, employee_id=employee_id)

            if distance:
                df.at[index, 'Distance_km'] = distance
                df.at[index, 'Processing_Status'] = 'Complete'
                logger.info(f"  ✓ Distance: {distance} km")
            else:
                df.at[index, 'Processing_Status'] = 'Failed'
                failed_addresses.append((employee_id, address))
                logger.warning(f"  ✗ Failed to get distance")

            processed += 1

            # Save progress every batch_size rows
            if processed % batch_size == 0:
                self.save_progress(df)
                logger.info(f"Progress saved: {processed} rows processed")
                time.sleep(5)  # Longer pause between batches

            # Regular pause between requests
            time.sleep(2)

        # Final save
        self.driver.quit()
        output_file = self.save_progress(df, final=True)

        # Report
        logger.info("\n" + "=" * 50)
        logger.info("PROCESSING COMPLETE")
        logger.info(f"Total processed: {processed}")
        logger.info(f"Successful: {len(df[df['Processing_Status'] == 'Complete'])}")
        logger.info(f"Failed: {len(failed_addresses)}")

        if failed_addresses:
            logger.info("\nFailed addresses:")
            for emp_id, addr in failed_addresses[:10]:  # Show first 10
                logger.info(f"  ID {emp_id}: {addr}")

        return df

    def save_progress(self, df, final=False):
        """Save progress to file with worker-specific naming"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Worker-specific prefix
        worker_suffix = f'_worker{self.worker_id}' if self.worker_id > 0 else ''

        if final:
            output_file = self.csv_file.replace('.csv', f'{worker_suffix}_distances_final.csv')
        else:
            output_file = self.csv_file.replace('.csv', f'{worker_suffix}_distances_progress.csv')

        df.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
        return output_file


# Helper functions for retry mode
def get_null_distance_rows(csv_file):
    """
    Identify rows with null/empty distances in the final CSV file.
    Returns a list of row indices that need to be processed.
    """
    # Try to read the final CSV file
    final_csv = csv_file.replace('.csv', '_distances_final.csv')

    if not os.path.exists(final_csv):
        print(f"Error: Final CSV file not found: {final_csv}")
        print("Please run the tool normally first to create the final CSV file.")
        sys.exit(1)

    # Read the final CSV
    df = pd.read_csv(final_csv, delimiter=';', encoding='utf-8-sig')

    # Find rows where Distance_km is null, empty, or NaN
    null_rows = []
    for idx, row in df.iterrows():
        distance = row.get('Distance_km')
        # Check if distance is null, NaN, empty string, or whitespace
        if pd.isna(distance) or (isinstance(distance, str) and distance.strip() == ''):
            null_rows.append(idx)

    return null_rows, df


# Parallel processing functions
def process_worker(worker_id, csv_file, company_address, start_row, end_row, debug_mode, headless):
    """Worker function for parallel processing"""
    try:
        print(f"Worker {worker_id} starting: rows {start_row} to {end_row-1}")

        calculator = GoogleMapsDistanceCalculator(
            csv_file_path=csv_file,
            company_address=company_address,
            start_row=start_row,
            end_row=end_row,
            debug_mode=debug_mode,
            worker_id=worker_id,
            headless=headless
        )

        result = calculator.process_csv_batch(batch_size=50)
        print(f"Worker {worker_id} completed successfully")
        return worker_id, True

    except Exception as e:
        print(f"Worker {worker_id} failed: {e}")
        return worker_id, False


def process_worker_retry(worker_id, csv_file, company_address, specific_rows, debug_mode, headless):
    """Worker function for retry mode - processes specific row indices"""
    try:
        print(f"Worker {worker_id} starting: {len(specific_rows)} rows to retry")

        # For retry mode, use the final CSV file
        final_csv = csv_file.replace('.csv', '_distances_final.csv')

        calculator = GoogleMapsDistanceCalculator(
            csv_file_path=final_csv,
            company_address=company_address,
            start_row=0,  # Not used when specific_rows is provided
            end_row=None,
            debug_mode=debug_mode,
            worker_id=worker_id,
            headless=headless
        )

        result = calculator.process_csv_batch(batch_size=50, specific_rows=specific_rows)
        print(f"Worker {worker_id} completed successfully")
        return worker_id, True

    except Exception as e:
        print(f"Worker {worker_id} failed: {e}")
        return worker_id, False


def merge_worker_results(csv_file, num_workers):
    """Merge results from all workers into final output"""
    print("\n" + "=" * 50)
    print("MERGING WORKER RESULTS")
    print("=" * 50)

    # Read original CSV
    df_main = pd.read_csv(csv_file, delimiter=';', encoding='utf-8-sig')

    # Ensure columns exist
    if 'Distance_km' not in df_main.columns:
        df_main['Distance_km'] = None
    if 'Processing_Status' not in df_main.columns:
        df_main['Processing_Status'] = 'Pending'

    # Merge each worker's results
    for worker_id in range(1, num_workers + 1):
        worker_file = csv_file.replace('.csv', f'_worker{worker_id}_distances_final.csv')

        if os.path.exists(worker_file):
            print(f"Merging results from worker {worker_id}...")
            df_worker = pd.read_csv(worker_file, delimiter=';', encoding='utf-8-sig')

            # Update main dataframe with worker's results
            for idx, row in df_worker.iterrows():
                if pd.notna(row.get('Distance_km')):
                    df_main.at[idx, 'Distance_km'] = row['Distance_km']
                if pd.notna(row.get('Processing_Status')):
                    df_main.at[idx, 'Processing_Status'] = row['Processing_Status']
        else:
            print(f"Warning: Worker {worker_id} output file not found: {worker_file}")

    # Save final merged output
    output_file = csv_file.replace('.csv', '_distances_final.csv')
    df_main.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')

    # Generate summary
    total_rows = len(df_main)
    completed = len(df_main[df_main['Processing_Status'] == 'Complete'])
    failed = len(df_main[df_main['Processing_Status'] == 'Failed'])
    pending = total_rows - completed - failed

    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    print(f"Total rows: {total_rows}")
    print(f"Completed: {completed} ({completed/total_rows*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total_rows*100:.1f}%)")
    print(f"Pending: {pending} ({pending/total_rows*100:.1f}%)")
    print(f"\nFinal output saved to: {output_file}")

    return output_file


def run_parallel_processing(csv_file, company_address, num_workers, debug_mode=False, headless=True):
    """Coordinate parallel processing across multiple workers"""
    print("=" * 50)
    print(f"PARALLEL PROCESSING WITH {num_workers} WORKERS")
    print("=" * 50)

    # Read CSV to determine row counts
    df = pd.read_csv(csv_file, delimiter=';', encoding='utf-8-sig')
    total_rows = len(df)

    # Calculate rows per worker
    rows_per_worker = total_rows // num_workers
    remainder = total_rows % num_workers

    print(f"Total rows to process: {total_rows}")
    print(f"Rows per worker: ~{rows_per_worker}")
    print(f"Headless mode: {headless}")
    print()

    # Create worker processes
    processes = []
    for worker_id in range(1, num_workers + 1):
        start_row = (worker_id - 1) * rows_per_worker
        # Give remainder rows to last worker
        if worker_id == num_workers:
            end_row = total_rows
        else:
            end_row = start_row + rows_per_worker

        print(f"Starting worker {worker_id}: rows {start_row} to {end_row-1} ({end_row - start_row} rows)")

        p = Process(
            target=process_worker,
            args=(worker_id, csv_file, company_address, start_row, end_row, debug_mode, headless)
        )
        p.start()
        processes.append(p)

    print("\nAll workers started. Press Ctrl+C to stop.")
    print("Monitor individual worker logs: worker_1_distance_calculator.log, worker_2_distance_calculator.log, etc.\n")

    # Wait for all workers to complete
    try:
        for p in processes:
            p.join()
        print("\nAll workers completed!")
    except KeyboardInterrupt:
        print("\n\nInterrupting workers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("All workers stopped. Progress has been saved.")

    # Merge results
    final_output = merge_worker_results(csv_file, num_workers)

    return final_output


def run_parallel_retry(csv_file, company_address, num_workers, debug_mode=False, headless=True):
    """Coordinate parallel retry processing for rows with null distances"""
    print("=" * 50)
    print(f"PARALLEL RETRY MODE WITH {num_workers} WORKERS")
    print("=" * 50)

    # Get rows that need to be retried
    null_rows, df = get_null_distance_rows(csv_file)

    if len(null_rows) == 0:
        print("No rows with null distances found. All rows have been processed!")
        return

    print(f"Found {len(null_rows)} rows with null distances to retry")
    print(f"Distributing across {num_workers} workers")
    print(f"Headless mode: {headless}")
    print()

    # Distribute null rows across workers
    rows_per_worker = len(null_rows) // num_workers
    remainder = len(null_rows) % num_workers

    # Create worker processes
    processes = []
    start_idx = 0

    for worker_id in range(1, num_workers + 1):
        # Calculate how many rows this worker gets
        worker_row_count = rows_per_worker + (1 if worker_id <= remainder else 0)
        end_idx = start_idx + worker_row_count

        # Get the specific row indices for this worker
        worker_rows = null_rows[start_idx:end_idx]

        if len(worker_rows) == 0:
            print(f"Worker {worker_id}: No rows assigned (all distributed to other workers)")
            continue

        print(f"Starting worker {worker_id}: {len(worker_rows)} rows to process")

        p = Process(
            target=process_worker_retry,
            args=(worker_id, csv_file, company_address, worker_rows, debug_mode, headless)
        )
        p.start()
        processes.append(p)

        start_idx = end_idx

    print("\nAll workers started. Press Ctrl+C to stop.")
    print("Monitor individual worker logs: worker_1_distance_calculator.log, worker_2_distance_calculator.log, etc.\n")

    # Wait for all workers to complete
    try:
        for p in processes:
            p.join()
        print("\nAll workers completed!")
    except KeyboardInterrupt:
        print("\n\nInterrupting workers...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.join()
        print("All workers stopped. Progress has been saved.")

    # Merge results
    final_output = merge_worker_results(csv_file, num_workers)

    return final_output


# Main execution
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Calculate distances from Google Maps')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with verbose logging and screenshots')
    parser.add_argument('--debug-first', action='store_true', help='Debug mode: process only first record')
    parser.add_argument('--start-row', type=int, default=0, help='Row number to start from (for resuming in single mode)')
    parser.add_argument('--csv', type=str, default="Employees QMH.csv", help='CSV file path')
    parser.add_argument('--company-address', type=str, default="Quanta Computer, F32Q+68X, Mỹ Lộc, Nam Định, Vietnam", help='Company address')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (1-10, default: 1 for single mode)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser window)')
    parser.add_argument('--retry-failed', action='store_true', help='Retry only rows with null/empty distances from the final CSV file')

    args = parser.parse_args()

    # Validate workers
    if args.workers < 1 or args.workers > 10:
        print("Error: --workers must be between 1 and 10")
        sys.exit(1)

    # Configuration
    CSV_FILE = args.csv
    COMPANY_ADDRESS = args.company_address
    START_ROW = args.start_row
    DEBUG_MODE = args.debug or args.debug_first
    NUM_WORKERS = args.workers

    # Auto-enable headless for parallel processing
    HEADLESS = args.headless or (NUM_WORKERS > 1)

    # Check if retry mode is enabled
    if args.retry_failed:
        # Retry mode: process only rows with null distances
        if NUM_WORKERS > 1:
            # Parallel retry mode
            print(f"\n{'='*50}")
            print(f"STARTING PARALLEL RETRY MODE")
            print(f"{'='*50}")
            print(f"Workers: {NUM_WORKERS}")
            print(f"CSV File: {CSV_FILE}")
            print(f"Headless Mode: {HEADLESS}")
            print(f"{'='*50}\n")

            result = run_parallel_retry(
                csv_file=CSV_FILE,
                company_address=COMPANY_ADDRESS,
                num_workers=NUM_WORKERS,
                debug_mode=DEBUG_MODE,
                headless=HEADLESS
            )
        else:
            # Single retry mode
            print(f"\n{'='*50}")
            print(f"STARTING SINGLE RETRY MODE")
            print(f"{'='*50}")

            # Get rows that need to be retried
            null_rows, df = get_null_distance_rows(CSV_FILE)

            if len(null_rows) == 0:
                print("No rows with null distances found. All rows have been processed!")
                sys.exit(0)

            print(f"Found {len(null_rows)} rows with null distances to retry")
            print(f"{'='*50}\n")

            # Use the final CSV file for retry
            final_csv = CSV_FILE.replace('.csv', '_distances_final.csv')

            calculator = GoogleMapsDistanceCalculator(
                final_csv,
                COMPANY_ADDRESS,
                start_row=0,
                debug_mode=DEBUG_MODE,
                headless=HEADLESS
            )

            result = calculator.process_csv_batch(batch_size=50, specific_rows=null_rows)

    # Normal processing mode
    elif NUM_WORKERS > 1:
        # Parallel processing mode
        print(f"\n{'='*50}")
        print(f"STARTING PARALLEL PROCESSING")
        print(f"{'='*50}")
        print(f"Workers: {NUM_WORKERS}")
        print(f"CSV File: {CSV_FILE}")
        print(f"Headless Mode: {HEADLESS}")
        print(f"{'='*50}\n")

        result = run_parallel_processing(
            csv_file=CSV_FILE,
            company_address=COMPANY_ADDRESS,
            num_workers=NUM_WORKERS,
            debug_mode=DEBUG_MODE,
            headless=HEADLESS
        )

    # Single processing mode
    else:
        # Initialize calculator
        calculator = GoogleMapsDistanceCalculator(
            CSV_FILE,
            COMPANY_ADDRESS,
            start_row=START_ROW,
            debug_mode=DEBUG_MODE,
            headless=HEADLESS
        )

        # Process CSV
        if args.debug_first:
            logger.info("Debug mode: Processing only first record")
            # Temporarily limit to first record
            df = pd.read_csv(CSV_FILE, delimiter=';', encoding='utf-8-sig')
            if len(df) > 1:
                # Save original and create temp file with just first row
                temp_csv = CSV_FILE.replace('.csv', '_debug_first.csv')
                df.iloc[START_ROW:START_ROW+1].to_csv(temp_csv, index=False, sep=';', encoding='utf-8-sig')
                calculator.csv_file = temp_csv
                logger.info(f"Created temporary CSV with first record: {temp_csv}")

        result = calculator.process_csv_batch(batch_size=50)