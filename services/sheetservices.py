import logging
from typing import List, Optional
import gspread
from google.oauth2.service_account import Credentials
from models.product import Product, ImageRecord

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetService:
    def __init__(self, config):
        self.config = config
        self.client = self._authenticate()
        self.sheet = self._open_sheet()
        self.headers: List[str] = []
        self.header_index: dict = {}  # column_name -> 0-based index

    # ------------------------------------------------------------------ #
    # Auth & connection
    # ------------------------------------------------------------------ #

    def _authenticate(self) -> gspread.Client:
        creds = Credentials.from_service_account_file(
            self.config.gsheet_credentials_path, scopes=SCOPES
        )
        return gspread.authorize(creds)

    def _open_sheet(self) -> gspread.Worksheet:
        spreadsheet = self.client.open_by_key(self.config.gsheet_spreadsheet_id)
        return spreadsheet.worksheet(self.config.gsheet_sheet_name)

    # ------------------------------------------------------------------ #
    # Header resolution
    # ------------------------------------------------------------------ #

    def _load_headers(self) -> None:
        """Read first row and build a name→index lookup."""
        self.headers = self.sheet.row_values(1)
        self.header_index = {name: idx for idx, name in enumerate(self.headers)}
        logger.info(f"Sheet headers loaded: {self.headers}")

    def _col_letter(self, col_name: str) -> str:
        """Convert a column name to its A1-notation letter (e.g. 'D')."""
        idx = self.header_index[col_name]  # 0-based
        # Simple conversion for up to 26 columns; extend if needed
        return chr(ord("A") + idx)

    def _ensure_output_columns(self) -> None:
        """Add output_image_1/2/3 headers if they don't exist yet."""
        output_cols = self.config.col_output_images
        changed = False
        for col_name in output_cols:
            if col_name not in self.header_index:
                self.headers.append(col_name)
                new_idx = len(self.headers) - 1
                self.header_index[col_name] = new_idx
                col_letter = self._col_letter(col_name)
                self.sheet.update(f"{col_letter}1", [[col_name]])
                logger.info(f"Created missing output column: {col_name}")
                changed = True
        if changed:
            logger.info("Output columns verified/created in sheet.")

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    def fetch_unprocessed_products(self) -> List[Product]:
        """
        Return Product objects for rows where ALL output columns are empty.
        Rows with any output already filled are skipped (already processed).
        """
        self._load_headers()
        self._ensure_output_columns()

        all_rows = self.sheet.get_all_values()
        data_rows = all_rows[1:]  # skip header row

        output_col_indices = [
            self.header_index[col] for col in self.config.col_output_images
        ]
        pid_idx = self.header_index[self.config.col_product_id]
        cat_idx = self.header_index[self.config.col_category]
        img_indices = [
            self.header_index[col]
            for col in self.config.col_image_links
            if col in self.header_index
        ]

        products: List[Product] = []
        for model_index, row in enumerate(data_rows):
            # Pad short rows to avoid index errors
            row = row + [""] * (len(self.headers) - len(row))

            # Skip if any output column already has a value
            if any(row[i].strip() for i in output_col_indices):
                logger.debug(f"Skipping already-processed row: {row[pid_idx]}")
                continue

            product_id = row[pid_idx].strip()
            category = row[cat_idx].strip()

            if not product_id:
                logger.warning(f"Empty product_id at row {model_index + 2}, skipping.")
                continue

            raw_urls = [row[i].strip() for i in img_indices]
            raw_urls = [u for u in raw_urls if u]  # drop empty URLs

            if not raw_urls:
                logger.warning(f"No image URLs for product {product_id}, skipping.")
                continue

            product = Product(
                product_id=product_id,
                category=category,
                raw_image_urls=raw_urls,
                model_index=model_index,
            )
            product.build_image_records()
            products.append(product)

        logger.info(f"Fetched {len(products)} unprocessed products from sheet.")
        return products

    # ------------------------------------------------------------------ #
    # Write
    # ------------------------------------------------------------------ #

    def write_output_urls(self, product_id: str, output_urls: List[Optional[str]]) -> None:
        """
        Write up to 3 output URLs back into the output_image_1/2/3 columns
        for the given product's row.
        """
        # Find the row number (1-based, +1 for header)
        all_pids = self.sheet.col_values(self.header_index[self.config.col_product_id] + 1)
        try:
            row_number = all_pids.index(product_id) + 1  # Changed from product.product_id
        except ValueError:
            logger.error(f"Product {product_id} not found in sheet for writing.")
            return

        for i, col_name in enumerate(self.config.col_output_images):
            url = output_urls[i] if i < len(output_urls) else None
            if url:
                col_letter = self._col_letter(col_name)
                self.sheet.update(f"{col_letter}{row_number}", [[url]])
                logger.info(f"Written {col_name} for {product_id}: {url}")  # Changed here too

    def write_error_flag(self, product: Product, message: str) -> None:
        """Write an error message into output_image_1 column so the row is not reprocessed."""
        self.write_output_urls(product, [f"ERROR: {message}", "", ""])