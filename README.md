# Bybit Historical Data Downloader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PyPI version](https://badge.fury.io/py/bybit-history.svg)](https://pypi.org/project/bybit-history/) [![Python Version](https://img.shields.io/pypi/pyversions/bybit-history)](https://pypi.org/project/bybit-history/) [![GitHub](https://img.shields.io/badge/GitHub-suenot%2Fbybit--history-blue?logo=github)](https://github.com/suenot/bybit-history)

This script downloads historical market data (trades, klines, etc.) for specified cryptocurrency pairs from the Bybit public data repository ([https://public.bybit.com/](https://public.bybit.com/)). It allows filtering by date range, coin pairs, and data types, organizing the downloaded and extracted CSV files into a structured directory format.

## Features

*   **Command-line Interface:** Configure downloads using CLI arguments.
*   **Flexible Filtering:**
    *   Specify start and end dates (`--start-date`, `--end-date`).
    *   Select specific coin pairs (e.g., `BTCUSDT,ETHUSDT`) or download all (`--coins ALL`).
    *   Choose data types (e.g., `trading,spot`) or download all (`--data-types ALL`).
*   **Optimized Coin Access:** Direct access to specified coins without scanning all directories when specific coins are requested.
*   **Intelligent Name Detection:** Extracts coin name from both file name and directory path.
*   **Organized Output:** Data is saved to a specified output directory (`--output-dir`, default `./data`), with subdirectories for each data type (e.g., `./data/trading/`, `./data/spot/`).
*   **Recursive Directory Traversal:** Handles different directory structures found in the Bybit repository (e.g., flat file lists, coin-based subdirectories, year-based subdirectories).
*   **Automatic Extraction:** Downloads `.csv.gz` archives, extracts them to `.csv`, and removes the archives.
*   **Skip Existing:** Avoids re-downloading and extracting files if the `.csv` file already exists.
*   **Basic Logging:** Provides informative output about the download process.

## Requirements

*   Python 3.8+
*   Libraries: `requests`, `beautifulsoup4`

## Installation (using Poetry)

1.  **Install Poetry:** Follow the instructions at [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
2.  **Clone the repository:**
    ```bash
    git clone https://github.com/suenot/bybit-history
    cd bybit-history
    ```
3.  **Install dependencies:**
    ```bash
    poetry install
    ```

## Usage

### Using Poetry Script (Recommended)

```bash
poetry run start --start-date <YYYY-MM-DD> --coins <COINS> [OPTIONS]
```

### Alternative Method

```bash
poetry run python bybit_data_downloader.py --start-date <YYYY-MM-DD> --coins <COINS> [OPTIONS]
```

**Required Arguments:**

*   `--start-date <YYYY-MM-DD>`: The earliest date for data to download.
*   `--coins <COINS>`: Comma-separated list of coin pairs (e.g., `BTCUSDT,ETHUSDT`) or `ALL` to attempt downloading all found pairs.

**Optional Arguments:**

*   `--end-date <YYYY-MM-DD>`: The latest date for data to download. If omitted, downloads up to the most recent available data.
*   `--data-types <TYPES>`: Comma-separated list of data types (e.g., `trading,spot`) or `ALL`. Defaults to `trading`. Known types: `trading`, `spot`, `kline_for_metatrader4`, `premium_index`, `spot_index`.
*   `--output-dir <PATH>`: Directory to save the data. Defaults to `./data`.
*   `--base-url <URL>`: Base URL for the Bybit public data. Defaults to `https://public.bybit.com/`.
*   `--version`: Show script version and exit.
*   `--help`: Show help message and exit.

**Example:**

```bash
poetry run start --start-date 2023-01-01 --end-date 2023-01-31 --coins BTCUSDT,ETHUSDT --data-types trading,spot --output-dir ./bybit_data
```

## Algorithm Overview

```mermaid
flowchart TD
    A[Start] --> B{Parse CLI Args};
    B --> C[Create Output Directory];
    C --> D{Fetch Base URL HTML};
    D --> E{Extract Data Type Links};
    E --> F{Loop Through Requested Data Types};
    F -- For Each Type --> G[Create Data Type Directory];
    G --> H{Coins = ALL?};
    H -- No --> DirectAccess[Direct Access to Specific Coins];
    DirectAccess --> I1{Loop Through Requested Coins};
    I1 -- For Each Coin --> J1[Construct Coin URL];
    J1 --> K1{Coin Exists on Server?};
    K1 -- Yes --> L1(Call process_directory);
    L1 --> I1;
    K1 -- No --> M1[Log Warning & Skip];
    M1 --> I1;
    I1 -- Loop Finished --> F;
    H -- Yes --> N[Construct Type URL & Path];
    N --> O(Call process_directory);
    O --> F;
    F -- Loop Finished --> Z[End];

    subgraph process_directory [process_directory]
        L1 & O --> P{Fetch Directory HTML};
        P --> Q{Find .csv.gz Links};
        Q --> R{Loop Through Files};
        R -- For Each File --> T{Extract Date};
        T --> U{Filter by Date?};
        U -- Yes --> V{Extract Coin from Name?};
        V -- Yes --> W{Filter by Coin?};
        W -- Yes --> X{Build Paths};
        X --> Y{File Exists?};
        Y -- No --> AA(Call download_and_extract);
        Y -- Yes --> R;
        AA --> R;
        W -- No --> X; 
        V -- No --> BB{Extract Coin from Path?};
        BB -- Yes --> W;
        BB -- No --> X;
        U -- No --> R;
        R -- Loop Finished --> CC{Find Subdirectory Links};
        CC --> DD{Loop Through Subdirs};
        DD -- For Each Subdir --> EE{Build Next URL & Path};
        EE --> FF{Filter by Coin?};
        FF -- Yes --> GG(Recursive Call process_directory);
        GG --> DD;
        FF -- No --> DD;
        DD -- Loop Finished --> HH[Return Counts];
    end

    subgraph download_and_extract [download_and_extract]
        AA --> AA1{Download .gz?};
        AA1 -- Success --> AA2{Extract .csv?};
        AA2 -- Success --> AA3{Remove .gz};
        AA3 --> AA4[Return Success];
        AA1 -- Fail --> AA5[Log Error & Cleanup];
        AA2 -- Fail --> AA5;
        AA5 --> AA6[Return Failure];
    end
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if available). 

## Documentation

Подробная документация по использованию и реализации доступна:

* **Основная документация** - В этом README файле описаны основные функции и примеры использования
* **Исходный код** - Доступен для просмотра в [репозитории GitHub](https://github.com/suenot/bybit-history)
* **Примеры API** - Можно посмотреть в файле [example_of_api.md](example_of_api.md)
* **Схема алгоритма** - Представлена в разделе "Algorithm Overview" выше 