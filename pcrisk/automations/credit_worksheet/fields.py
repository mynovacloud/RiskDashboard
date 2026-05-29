import re
from dataclasses import dataclass, field
from typing import Optional

FIELD_DEFINITIONS = [
    {"expression": "940", "label": "Total Assets", "excel_cell": "B4"},
    {"expression": "1800", "label": "Total Equity", "excel_cell": "B6"},
    {"expression": "750", "label": "Cash and cash equivalents", "excel_cell": "B8"},
    {"expression": "760", "label": "Cash segregated under federal", "excel_cell": "B10"},
    {"expression": "770", "label": "Fails to Deliver", "excel_cell": "B12"},
    {"expression": "780", "label": "Stocks Borrowed", "excel_cell": "B14"},
    {"expression": "800", "label": "Clearing Org receivables", "excel_cell": "B16"},
    {"expression": "810", "label": "Others", "excel_cell": "B18"},
    {"expression": "820", "label": "Customer Receivables", "excel_cell": "B20"},
    {"expression": "840", "label": "Reverse Repos", "excel_cell": "B22"},
    {"expression": "292", "label": "Trade Date Receivable", "excel_cell": "B24"},
    {"expression": "12019", "label": "Marketable securities", "excel_cell": "B26"},
    {"expression": "740", "label": "Non-allowable assets", "excel_cell": "B28"},
    {"expression": "890", "label": "Secured Demand Notes", "excel_cell": "B32"},
    {"expression": "1760", "label": "Total Liabilities", "excel_cell": "B34"},

    {"expression": "1490+1500", "label": "Fails to Receive", "excel_cell": "D12"},
    {"expression": "1510+1520", "label": "Stocks Loaned", "excel_cell": "D14"},
    {"expression": "1550+1560", "label": "Clearing Org payables", "excel_cell": "D16"},
    {"expression": "1570", "label": "Other", "excel_cell": "D18"},
    {"expression": "1580+1590", "label": "Customer payables", "excel_cell": "D20"},
    {"expression": "1480", "label": "Repos", "excel_cell": "D22"},
    {"expression": "1686", "label": "Obligation to rtn Securities Collateral", "excel_cell": "D26"},
    {"expression": "1480", "label": "All other liabilities", "excel_cell": "D30"},
    {"expression": "1730", "label": "Securities borrowings", "excel_cell": "D32"},
]


AMOUNT_PATTERN = re.compile(
    r"""
    ^\$?
    \(?
    -?
    (?:
        \d{1,3}(?:,\d{3})+ |
        \d+
    )
    (?:\.\d+)?
    \)?
    $
    """,
    re.VERBOSE,
)


@dataclass
class WordItem:
    page_index: int
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_no: int
    line_no: int
    word_no: int

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2


@dataclass
class CodeOccurrence:
    code: str
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    nearby_amount_text: str = ""
    nearby_context: str = ""
    note: str = ""
    confidence_score: int = 0
    selected: bool = False

    @property
    def location_text(self) -> str:
        return f"Page {self.page_number}, x={round(self.x0, 2)}, y={round(self.y0, 2)}"


@dataclass
class FieldSpec:
    expression: str
    label: str
    excel_cell: str
    codes: list[str] = field(default_factory=list)


@dataclass
class FieldResult:
    expression: str
    label: str
    excel_cell: str
    display_value: str
    numeric_value: Optional[float]
    should_write_blank: bool
    status: str
    difficulty: str
    notes: str
    component_details: str
