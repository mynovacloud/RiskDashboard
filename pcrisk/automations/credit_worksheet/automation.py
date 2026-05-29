from pcrisk.automations.base import Automation, register
from pcrisk.automations.credit_worksheet.routes import router

automation = register(
    Automation(
        slug="credit_worksheet",
        name="Credit Worksheet",
        description=(
            "Upload customer PDF files and automatically produce completed "
            "Excel credit worksheets using the backend template."
        ),
        router=router,
        mount_prefix="",
        nav_label="Home",
        is_primary=True,
    )
)
