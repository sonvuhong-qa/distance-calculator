# Google Maps Distance Calculator

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

Automated tool to calculate driving distances between addresses using Google Maps via Selenium WebDriver. Perfect for HR/admin teams calculating employee commute distances at scale.

## Features

- **Automated Distance Calculation** - Uses Google Maps Directions via browser automation
- **CSV Batch Processing** - Read/write semicolon-delimited CSV files with UTF-8 encoding
- **Parallel Processing** - Run 1-10 workers simultaneously for faster processing
- **Automatic Retry** - Failed lookups retry up to 3 times with exponential backoff (3s, 6s, 9s)
- **Progress Persistence** - Saves progress every 50 rows, never lose your work
- **Resume Capability** - Start from any row number to continue interrupted jobs
- **Debug Mode** - Capture screenshots and HTML dumps for troubleshooting
- **Headless Support** - Run without visible browser window
- **Unit Conversion** - Automatically converts miles to kilometers

## Prerequisites

- **Python 3.10** or higher
- **Google Chrome** browser (latest version recommended)
- **Internet connection**
- ChromeDriver (automatically managed - no manual installation needed)

## Installation

```bash
# Clone the repository
git clone https://github.com/sonvuhong-qa/distance-calculator.git
cd distance-calculator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. **Prepare your CSV file** with columns `ID` and `Residence address`:
   ```csv
   ID;Residence address
   EMP001;123 Main Street, City, Country
   EMP002;456 Oak Avenue, Town, Country
   ```

2. **Run the tool**:
   ```bash
   python distance_calculator_tool.py --csv "employees.csv" --company-address "Your Company Address"
   ```

3. **Find results** in `employees_distances_final.csv`

## Usage

### Basic Single Mode

Process addresses one at a time with a visible browser:

```bash
python distance_calculator_tool.py --csv "employees.csv" --company-address "123 Main St, City"
```

### Parallel Processing (Recommended for Large Files)

Use multiple workers for faster processing (auto-enables headless mode):

```bash
python distance_calculator_tool.py --csv "employees.csv" --company-address "123 Main St" --workers 4
```

### Headless Mode

Run without visible browser window:

```bash
python distance_calculator_tool.py --csv "employees.csv" --company-address "123 Main St" --headless
```

### Resume from Specific Row

Continue processing from a specific row number:

```bash
python distance_calculator_tool.py --csv "employees.csv" --company-address "123 Main St" --start-row 500
```

### Retry Failed Rows

Re-process only rows that failed or have empty distances:

```bash
python distance_calculator_tool.py --csv "employees.csv" --retry-failed
```

Parallel retry mode:

```bash
python distance_calculator_tool.py --csv "employees.csv" --retry-failed --workers 4
```

### Debug Mode

Enable verbose logging with screenshots saved to `debug_screenshots/`:

```bash
python distance_calculator_tool.py --csv "employees.csv" --debug
```

Test with only the first row:

```bash
python distance_calculator_tool.py --csv "employees.csv" --debug-first
```

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--csv` | string | `Employees QMH.csv` | Path to input CSV file |
| `--company-address` | string | Quanta Computer Vietnam | Destination address for distance calculation |
| `--workers` | int | `1` | Number of parallel workers (1-10) |
| `--start-row` | int | `0` | Row number to start from (0-indexed) |
| `--headless` | flag | `False` | Run browser without visible window |
| `--retry-failed` | flag | `False` | Only process rows with null/empty distances |
| `--debug` | flag | `False` | Enable verbose logging and save screenshots |
| `--debug-first` | flag | `False` | Process only the first row for testing |

## Data Format

### Input CSV

| Requirement | Value |
|-------------|-------|
| Delimiter | Semicolon (`;`) |
| Encoding | UTF-8 (with or without BOM) |
| Required columns | `ID`, `Residence address` |

**Example:**
```csv
ID;Residence address
V4060052;123 Nguyen Trai, Hanoi, Vietnam
V4090259;456 Le Loi, Ho Chi Minh City, Vietnam
```

### Output CSV

The tool creates `{original_filename}_distances_final.csv` with additional columns:

| Column | Description |
|--------|-------------|
| `Distance_km` | Calculated driving distance in kilometers |
| `Processing_Status` | `Pending`, `Complete`, or `Failed` |

**Example output:**
```csv
ID;Residence address;Distance_km;Processing_Status
V4060052;123 Nguyen Trai, Hanoi;45.2;Complete
V4090259;456 Le Loi, Ho Chi Minh City;;Failed
```

## How It Works

1. **Load CSV** - Reads addresses using pandas
2. **Initialize Browser** - Sets up Chrome with anti-detection features
3. **Navigate to Google Maps** - Opens the Directions page
4. **Enter Addresses** - Inputs origin (employee) and destination (company)
5. **Wait for Route** - Waits for Google Maps to calculate the route
6. **Extract Distance** - Parses distance using multiple CSS/XPath selectors
7. **Save Progress** - Writes results every 50 rows
8. **Retry on Failure** - Attempts up to 3 times with increasing delays

```
[CSV Input] -> [Selenium/Chrome] -> [Google Maps] -> [Distance Extraction] -> [CSV Output]
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **ChromeDriver version mismatch** | Delete `~/.wdm/` folder and re-run. The tool will auto-download the correct version. |
| **"No distance found" errors** | Run with `--debug` to see screenshots. Check that addresses are valid and specific. |
| **Rate limiting / CAPTCHA** | Reduce `--workers` count. Add longer delays between requests. Try `--headless` mode. |
| **Permission denied** | Check file permissions. Run from a directory with write access. |
| **Memory issues with many workers** | Reduce `--workers` count (try 2-4 instead of 10). |
| **Browser crashes** | Update Chrome to latest version. Try `--headless` mode. |
| **Timeout errors** | Check internet connection. Google Maps may be slow - the tool will retry automatically. |

### Log Files

- `distance_calculator.log` - Main execution log
- `worker_N_distance_calculator.log` - Per-worker logs (parallel mode)
- `distance_calculator_debug.log` - Detailed debug log (when using `--debug`)
- `debug_screenshots/` - Screenshots and HTML dumps (when using `--debug`)

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes:
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push** to the branch:
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

### Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use meaningful variable and function names
- Add docstrings for new functions
- Include error handling for edge cases

### Reporting Issues

When reporting bugs, please include:
- Python version (`python --version`)
- Chrome version
- Operating system
- Full error message and stack trace
- Steps to reproduce

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Selenium](https://selenium.dev/) - Browser automation framework
- [pandas](https://pandas.pydata.org/) - Data manipulation library
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) - Automatic ChromeDriver management

---

Made with determination to automate tedious distance calculations.
