import html
import re
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from pcrisk.core.auth import load_users
from pcrisk.core.config import load_config
from pcrisk.core.jobs import (
    build_full_console_text,
    get_file_size_label,
    get_job_payload,
    safe_js_json,
)
from pcrisk.core.paths import AUDIT_DIR, OUTPUT_DIR
from pcrisk.core.templates import get_logo_url, get_template_status
from pcrisk.ui.shell import head_html, hero_html, nav_html, topbar_html

def login_page_html(error: str = "") -> str:
    logo_url = get_logo_url()
    logo_block = ""
    if logo_url:
        logo_block = f'<div class="login-logo"><img src="{html.escape(logo_url)}" alt="PhillipCapital" /></div>'

    error_block = ""
    if error:
        error_block = f'<div class="login-error">{html.escape(error)}</div>'

    page = """
<!doctype html>
<html>
__HEAD__
<body>
<div class="shell">
    <div class="login-shell">
        <div class="login-card">
            <div class="login-topline"></div>
            <div class="login-body">
                __LOGO__
                <div class="login-title">Risk Management Portal</div>
                <div class="login-sub">Credit Worksheet Processor &middot; Sign in to continue</div>
                __ERROR__
                <form method="post" action="/login">
                    <div class="field-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" autocomplete="username" autofocus required />
                    </div>
                    <div class="field-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" autocomplete="current-password" required />
                    </div>
                    <button type="submit" class="orange full-btn">Sign In</button>
                </form>
            </div>
        </div>
    </div>
</div>
</body>
</html>
    """

    page = page.replace("__HEAD__", head_html("Sign In | Phillip Capital Risk Management"))
    page = page.replace("__LOGO__", logo_block)
    page = page.replace("__ERROR__", error_block)
    return page


def settings_page_html(user: str, flash: str = "", flash_type: str = "ok") -> str:
    config = load_config()
    users = load_users()

    flash_block = ""
    if flash:
        flash_block = f'<div class="flash {html.escape(flash_type)}">{html.escape(flash)}</div>'

    user_rows = []
    for record in sorted(users.values(), key=lambda r: r.get("username", "").lower()):
        uname = record.get("username", "")
        created_at = record.get("created_at", "")
        created_by = record.get("created_by", "")
        is_self = uname.strip().lower() == user.strip().lower()

        delete_control = (
            '<span class="muted" style="font-size:12px;">Current session</span>'
            if is_self
            else f"""
            <form method="post" action="/settings/delete-user" onsubmit="return confirm('Remove {html.escape(uname)}?');" style="margin:0;">
                <input type="hidden" name="username" value="{html.escape(uname)}" />
                <button type="submit" class="danger" style="padding:8px 12px; font-size:12px;">Remove</button>
            </form>
            """
        )

        pw_updated_at = record.get("password_updated_at", "")
        pw_updated_by = record.get("password_updated_by", "")
        if pw_updated_at:
            meta_pw_line = (
                f'<div class="ur-meta">Password updated {html.escape(pw_updated_at)}'
                f' by {html.escape(pw_updated_by)}</div>'
            )
        else:
            meta_pw_line = ""

        self_tag = '<span class="ur-self-tag">You</span>' if is_self else ""
        confirm_msg = (
            "Change your own password?"
            if is_self
            else f"Update password for {uname}? Any existing sessions for this user will be signed out."
        )

        user_rows.append(
            f"""
            <div class="user-row">
                <div class="ur-top">
                    <div style="min-width:0;">
                        <div class="ur-name">{html.escape(uname)}{self_tag}</div>
                        <div class="ur-meta">Added {html.escape(created_at)} by {html.escape(created_by)}</div>
                        {meta_pw_line}
                    </div>
                    <div>{delete_control}</div>
                </div>
                <form method="post" action="/settings/update-password" class="ur-pwform"
                      onsubmit="return confirm('{html.escape(confirm_msg)}');">
                    <input type="hidden" name="username" value="{html.escape(uname)}" />
                    <input type="password" name="new_password" placeholder="New password for {html.escape(uname)}"
                           required minlength="1" autocomplete="new-password" />
                    <button type="submit" class="primary">Update password</button>
                </form>
            </div>
            """
        )

    users_block = "".join(user_rows) if user_rows else '<p class="muted">No users found.</p>'

    page = """
<!doctype html>
<html>
__HEAD__
<body>
<div class="shell">
    __TOPBAR__
    __HERO__

    __FLASH__

    <div class="settings-grid">
        <div class="card">
            <h2>Login Credentials</h2>
            <p class="muted">Existing users who can sign in to the portal.</p>
            __USERS_BLOCK__
        </div>

        <div class="card">
            <h2>Add New Login</h2>
            <p class="muted">Create a username and password. Passwords are stored hashed.</p>
            <form method="post" action="/settings/add-user">
                <div class="field-group">
                    <label for="new_username">Username</label>
                    <input type="text" id="new_username" name="new_username" placeholder="name@phillipcapital.com" required />
                </div>
                <div class="field-group">
                    <label for="new_password">Password</label>
                    <input type="text" id="new_password" name="new_password" placeholder="Set a password" required />
                </div>
                <button type="submit" class="orange">Add User</button>
            </form>
        </div>
    </div>

    <div class="card">
        <h2>Upload Limits</h2>
        <p class="muted">Controls applied to every batch. Session timeout also signs users out after inactivity.</p>
        <form method="post" action="/settings/limits">
            <div class="limit-grid">
                <div class="field-group">
                    <label for="max_pdf_size_mb">Max PDF size (MB)</label>
                    <input type="number" min="1" max="500" id="max_pdf_size_mb" name="max_pdf_size_mb" value="__MAX_SIZE__" />
                </div>
                <div class="field-group">
                    <label for="max_batch_size">Max PDFs per batch</label>
                    <input type="number" min="1" max="200" id="max_batch_size" name="max_batch_size" value="__MAX_BATCH__" />
                </div>
                <div class="field-group">
                    <label for="session_timeout_minutes">Session timeout (minutes)</label>
                    <input type="number" min="5" max="1440" id="session_timeout_minutes" name="session_timeout_minutes" value="__TIMEOUT__" />
                </div>
            </div>
            <button type="submit">Save Limits</button>
        </form>
    </div>

    <div class="card">
        <h2>Cleanup</h2>
        <p class="muted">
            Automatic cleanup runs on startup. Uploads older than <strong>__CU_UPLOADS__</strong> days,
            outputs/audits older than <strong>__CU_OUTPUTS__</strong> days, and logs older than <strong>__CU_LOGS__</strong> days
            are removed. You can also change retention or clear folders now.
        </p>

        <form method="post" action="/settings/retention">
            <div class="limit-grid">
                <div class="field-group">
                    <label for="cleanup_uploads_days">Keep uploads (days)</label>
                    <input type="number" min="0" max="365" id="cleanup_uploads_days" name="cleanup_uploads_days" value="__CU_UPLOADS__" />
                </div>
                <div class="field-group">
                    <label for="cleanup_outputs_days">Keep outputs/audits (days)</label>
                    <input type="number" min="0" max="365" id="cleanup_outputs_days" name="cleanup_outputs_days" value="__CU_OUTPUTS__" />
                </div>
                <div class="field-group">
                    <label for="cleanup_logs_days">Keep logs (days)</label>
                    <input type="number" min="0" max="365" id="cleanup_logs_days" name="cleanup_logs_days" value="__CU_LOGS__" />
                </div>
            </div>
            <button type="submit">Save Retention</button>
        </form>

        <hr style="border:none; border-top:1px solid var(--border); margin:18px 0;" />

        <p class="muted">Run cleanup immediately:</p>
        <form method="post" action="/settings/cleanup" style="display:inline;">
            <input type="hidden" name="target" value="age" />
            <button type="submit" class="secondary">Run Age-Based Cleanup</button>
        </form>
        <form method="post" action="/settings/cleanup" style="display:inline;" onsubmit="return confirm('Clear ALL uploaded PDFs now?');">
            <input type="hidden" name="target" value="uploads" />
            <button type="submit" class="danger">Clear All Uploads</button>
        </form>
        <form method="post" action="/settings/cleanup" style="display:inline;" onsubmit="return confirm('Clear ALL logs now?');">
            <input type="hidden" name="target" value="logs" />
            <button type="submit" class="danger">Clear All Logs</button>
        </form>
        <form method="post" action="/settings/cleanup" style="display:inline;" onsubmit="return confirm('Clear ALL generated outputs and audits now?');">
            <input type="hidden" name="target" value="outputs" />
            <button type="submit" class="danger">Clear All Outputs</button>
        </form>
    </div>
</div>
</body>
</html>
    """

    page = page.replace("__HEAD__", head_html("Settings | Phillip Capital Risk Management"))
    page = page.replace("__TOPBAR__", topbar_html("settings", user))
    page = page.replace(
        "__HERO__",
        hero_html(
            "Settings",
            "Manage portal logins, upload limits, session timeout, and folder cleanup.",
        ),
    )
    page = page.replace("__FLASH__", flash_block)
    page = page.replace("__USERS_BLOCK__", users_block)
    page = page.replace("__MAX_SIZE__", str(config["max_pdf_size_mb"]))
    page = page.replace("__MAX_BATCH__", str(config["max_batch_size"]))
    page = page.replace("__TIMEOUT__", str(config["session_timeout_minutes"]))
    page = page.replace("__CU_UPLOADS__", str(config["cleanup_uploads_days"]))
    page = page.replace("__CU_OUTPUTS__", str(config["cleanup_outputs_days"]))
    page = page.replace("__CU_LOGS__", str(config["cleanup_logs_days"]))

    return page




def console_page_html(user: str, job_id: Optional[str] = None) -> str:
    try:
        payload = get_job_payload(job_id)
    except Exception:
        payload = {}

    console_text = build_full_console_text(payload) if payload else "No console data yet."
    payload_json = safe_js_json(payload)

    page = """
<!doctype html>
<html>
__HEAD__
<body>
<div class="shell">
    __TOPBAR__
    __HERO__

    <div class="card">
        <h2>Run Summary</h2>
        <div id="summaryBox" class="summary-list">No run found yet.</div>
        <br />
        <button onclick="copyEverything()">Copy Full Console</button>
        <button onclick="copyFieldResults()" class="secondary">Copy Field Results</button>
        <button onclick="copyRawOccurrences()" class="secondary">Copy Raw Occurrences</button>
        <button onclick="copyDebugLog()" class="secondary">Copy Debug Log</button>
    </div>

    <div class="card">
        <h2>Combined Console</h2>
        <div id="consoleBox" class="console">__CONSOLE_TEXT__</div>
    </div>
</div>

<script>
const payload = __PAYLOAD__;

let latestFieldResults = payload.field_results || [];
let latestRawOccurrences = payload.raw_occurrences || [];
let latestDebugLog = payload.debug_log || [];
let latestSummary = payload.summary || [];

if (payload.type === "batch" && payload.batch_results && payload.batch_results.length > 0) {
    const firstSuccess = payload.batch_results.find(item => item.status === "SUCCESS");
    if (firstSuccess) {
        latestFieldResults = firstSuccess.field_results || [];
        latestRawOccurrences = firstSuccess.raw_occurrences || [];
        latestDebugLog = firstSuccess.debug_log || [];
        latestSummary = payload.batch_summary || [];
    }
}

function rowsToTsv(rows) {
    return rows.map(row => row.map(cell => {
        if (cell === null || cell === undefined) return "";
        return String(cell).replaceAll("\\t", " ").replaceAll("\\n", " ").replaceAll("\\r", " ").trim();
    }).join("\\t")).join("\\n");
}

function buildFieldResultsTsv() {
    const rows = [[
        "PDF Code(s)", "Field", "Excel Cell", "Preview Value", "Status", "Difficulty", "Notes", "Component Details"
    ]];
    latestFieldResults.forEach(r => rows.push([
        r.expression, r.label, r.excel_cell, r.display_value, r.status, r.difficulty, r.notes, r.component_details
    ]));
    return rowsToTsv(rows);
}

function buildRawOccurrencesTsv() {
    const rows = [[
        "Code", "Selected", "Page", "X0", "Y0", "X1", "Y1", "Nearby Amount", "Confidence Score", "Note", "Nearby Context"
    ]];
    latestRawOccurrences.forEach(r => rows.push([
        r.code, r.selected ? "YES" : "NO", r.page_number,
        Number(r.x0 || 0).toFixed(2), Number(r.y0 || 0).toFixed(2),
        Number(r.x1 || 0).toFixed(2), Number(r.y1 || 0).toFixed(2),
        r.nearby_amount_text, r.confidence_score, r.note, r.nearby_context
    ]));
    return rowsToTsv(rows);
}

function buildFullConsoleText() {
    return document.getElementById("consoleBox").textContent || "";
}

async function copyText(text, label) {
    if (!text || !text.trim()) { alert("No " + label + " available to copy."); return; }
    await navigator.clipboard.writeText(text);
    alert(label + " copied to clipboard.");
}

function copyEverything() { copyText(buildFullConsoleText(), "Full Console"); }
function copyFieldResults() { copyText(buildFieldResultsTsv(), "Field Results"); }
function copyRawOccurrences() { copyText(buildRawOccurrencesTsv(), "Raw Occurrences"); }
function copyDebugLog() { copyText(latestDebugLog.join("\\n"), "Debug Log"); }

function render() {
    if (payload.type === "batch") {
        document.getElementById("summaryBox").textContent = (payload.batch_summary || []).join("\\n") || "No run found yet.";
    } else {
        document.getElementById("summaryBox").textContent = latestSummary.join("\\n") || "No run found yet.";
    }
}

render();
</script>
</body>
</html>
    """

    page = page.replace("__HEAD__", head_html("Console | Phillip Capital Risk Management"))
    page = page.replace("__TOPBAR__", topbar_html("console", user))
    page = page.replace(
        "__HERO__",
        hero_html(
            "Processing Console",
            "Review field results, raw helper-code occurrences, and debug logs from the latest workbook generation.",
        ),
    )
    page = page.replace("__PAYLOAD__", payload_json)
    page = page.replace("__CONSOLE_TEXT__", html.escape(console_text))

    return page




def outputs_page_html(user: str) -> str:
    # ---- SVG icons (inline so they inherit currentColor) ----
    folder_svg = (
        '<svg viewBox="0 0 20 16" fill="currentColor" aria-hidden="true">'
        '<path d="M0 2.5C0 1.12 1.12 0 2.5 0H7l2 2h8.5C18.88 2 20 3.12 20 4.5v9c0 1.38-1.12 2.5-2.5 2.5h-15C1.12 16 0 14.88 0 13.5v-11z"/>'
        '</svg>'
    )
    doc_svg = (
        '<svg viewBox="0 0 16 20" fill="currentColor" aria-hidden="true">'
        '<path d="M2 0C0.9 0 0 0.9 0 2v16c0 1.1 0.9 2 2 2h12c1.1 0 2-0.9 2-2V6L10 0H2zm8 1.5L14.5 6H10V1.5z"/>'
        '</svg>'
    )
    audit_svg = (
        '<svg viewBox="0 0 16 20" fill="currentColor" aria-hidden="true">'
        '<path d="M2 0C0.9 0 0 0.9 0 2v16c0 1.1 0.9 2 2 2h12c1.1 0 2-0.9 2-2V2c0-1.1-0.9-2-2-2H2zm2 6h8v1.5H4V6zm0 3h8v1.5H4V9zm0 3h5v1.5H4V12z"/>'
        '</svg>'
    )

    def fmt_time(mtime: float) -> str:
        return datetime.fromtimestamp(mtime).strftime("%I:%M %p").lstrip("0")

    def fmt_size(n: int) -> str:
        return get_file_size_label(n)

    # ---- Discover ZIPs (each = one batch) and read members ----
    batches = []
    for zip_path in OUTPUT_DIR.glob("*.zip"):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                members = {n for n in zf.namelist() if not n.endswith("/")}
        except Exception:
            members = set()
        batches.append({
            "kind": "batch",
            "zip_path": zip_path,
            "members": members,
            "mtime": zip_path.stat().st_mtime,
            "files": [],   # populated below: list of {"xlsx_path", "audit_paths"}
        })

    # Map xlsx filename -> batch index (so xlsx files can be sorted into their folder)
    xlsx_to_batch = {}
    for idx, b in enumerate(batches):
        for name in b["members"]:
            xlsx_to_batch[name] = idx

    # ---- Index audits by xlsx stem (handles both "_audit" and "_audit_2" naming) ----
    audit_pattern = re.compile(r"^(.+?)_audit(?:_\d+)?$")
    audits_by_xlsx_stem: dict[str, list[Path]] = {}
    for audit_path in AUDIT_DIR.glob("*.txt"):
        m = audit_pattern.match(audit_path.stem)
        if m:
            audits_by_xlsx_stem.setdefault(m.group(1), []).append(audit_path)

    matched_audits: set[Path] = set()
    singles = []

    # ---- Walk xlsx files; classify each as batch member or single ----
    for xlsx_path in OUTPUT_DIR.glob("*.xlsx"):
        these_audits = audits_by_xlsx_stem.get(xlsx_path.stem, [])
        for a in these_audits:
            matched_audits.add(a)

        entry = {"xlsx_path": xlsx_path, "audit_paths": these_audits}

        if xlsx_path.name in xlsx_to_batch:
            batches[xlsx_to_batch[xlsx_path.name]]["files"].append(entry)
        else:
            singles.append({
                "kind": "single",
                "xlsx_path": xlsx_path,
                "audit_paths": these_audits,
                "mtime": xlsx_path.stat().st_mtime,
            })

    # ---- Orphan audits (xlsx no longer on disk) ----
    orphan_audits = []
    for audits in audits_by_xlsx_stem.values():
        for a in audits:
            if a not in matched_audits:
                orphan_audits.append({
                    "kind": "audit_only",
                    "audit_path": a,
                    "mtime": a.stat().st_mtime,
                })

    # ---- Combine + sort by mtime desc ----
    items = batches + singles + orphan_audits
    items.sort(key=lambda it: it["mtime"], reverse=True)

    # ---- Group by date ----
    today = date.today()
    yesterday = today - timedelta(days=1)

    def date_labels(d):
        if d == today:
            return "Today", d.strftime("%A, %B %d")
        if d == yesterday:
            return "Yesterday", d.strftime("%A, %B %d")
        if d.year == today.year:
            return d.strftime("%A, %B %d"), ""
        return d.strftime("%A, %B %d, %Y"), ""

    date_groups: list[tuple[date, list[dict]]] = []
    for it in items:
        d = datetime.fromtimestamp(it["mtime"]).date()
        if not date_groups or date_groups[-1][0] != d:
            date_groups.append((d, []))
        date_groups[-1][1].append(it)

    # ---- Renderers ----
    def render_file_row(entry):
        xlsx_path = entry["xlsx_path"]
        audit_paths = entry["audit_paths"]
        if not xlsx_path.exists():
            return ""
        stat = xlsx_path.stat()
        time_label = fmt_time(stat.st_mtime)
        size_label = fmt_size(stat.st_size)
        audit_btns = "".join(
            f'<a class="button-link secondary" href="/download-audit/{html.escape(a.name)}">Audit</a>'
            for a in audit_paths
        )
        return f"""
        <div class="file-row">
            <span class="file-icon xlsx">{doc_svg}</span>
            <div class="file-info">
                <div class="file-name">{html.escape(xlsx_path.name)}</div>
                <div class="file-meta">
                    <span>{html.escape(size_label)}</span>
                    <span class="dot">·</span>
                    <span>{html.escape(time_label)}</span>
                </div>
            </div>
            <div class="file-actions">
                <a class="button-link" href="/download-output/{html.escape(xlsx_path.name)}">Download</a>
                {audit_btns}
            </div>
        </div>
        """

    def render_batch(batch):
        zip_path = batch["zip_path"]
        files = batch["files"]
        n_files = len(files)
        n_audits = sum(len(e["audit_paths"]) for e in files)
        total_size = zip_path.stat().st_size
        for e in files:
            if e["xlsx_path"].exists():
                total_size += e["xlsx_path"].stat().st_size
            for a in e["audit_paths"]:
                if a.exists():
                    total_size += a.stat().st_size
        time_label = fmt_time(batch["mtime"])

        if not files:
            # ZIP with no surviving members
            inner = (
                '<p class="muted" style="margin:8px 0;">'
                'The individual workbooks for this batch are no longer on disk. '
                'You can still download the ZIP below.'
                '</p>'
            )
        else:
            inner = "".join(
                render_file_row(e)
                for e in sorted(files, key=lambda e: e["xlsx_path"].name.lower())
            )

        files_word = "workbook" if n_files == 1 else "workbooks"
        audits_word = "audit" if n_audits == 1 else "audits"

        return f"""
        <details class="folder-card" open>
            <summary>
                <span class="file-icon folder">{folder_svg}</span>
                <div class="folder-info">
                    <div class="folder-name">Batch &middot; {n_files} {files_word} &middot; {html.escape(time_label)}</div>
                    <div class="folder-meta">
                        <span>{n_audits} {audits_word}</span>
                        <span class="dot">·</span>
                        <span>{html.escape(fmt_size(total_size))}</span>
                        <span class="dot">·</span>
                        <code>{html.escape(zip_path.name)}</code>
                    </div>
                </div>
                <div class="folder-actions">
                    <a class="button-link orange" href="/download-output/{html.escape(zip_path.name)}">Download all (ZIP)</a>
                </div>
            </summary>
            <div class="folder-contents">
                {inner}
            </div>
        </details>
        """

    def render_single(item):
        xlsx_path = item["xlsx_path"]
        audit_paths = item["audit_paths"]
        if not xlsx_path.exists():
            return ""
        stat = xlsx_path.stat()
        time_label = fmt_time(stat.st_mtime)
        size_label = fmt_size(stat.st_size)
        audit_btns = "".join(
            f'<a class="button-link secondary" href="/download-audit/{html.escape(a.name)}">Audit</a>'
            for a in audit_paths
        )
        audit_word = "audit attached" if audit_paths else "no audit on file"
        return f"""
        <div class="single-card">
            <span class="file-icon xlsx">{doc_svg}</span>
            <div class="folder-info">
                <div class="folder-name">{html.escape(xlsx_path.name)}</div>
                <div class="folder-meta">
                    <span>Single workbook</span>
                    <span class="dot">·</span>
                    <span>{html.escape(size_label)}</span>
                    <span class="dot">·</span>
                    <span>{html.escape(time_label)}</span>
                    <span class="dot">·</span>
                    <span>{audit_word}</span>
                </div>
            </div>
            <div class="folder-actions">
                <a class="button-link orange" href="/download-output/{html.escape(xlsx_path.name)}">Download</a>
                {audit_btns}
            </div>
        </div>
        """

    def render_audit_only(item):
        audit_path = item["audit_path"]
        time_label = fmt_time(item["mtime"])
        size_label = fmt_size(audit_path.stat().st_size)
        return f"""
        <div class="single-card audit-only">
            <span class="file-icon audit">{audit_svg}</span>
            <div class="folder-info">
                <div class="folder-name">{html.escape(audit_path.name)}</div>
                <div class="folder-meta">
                    <span>Audit report only</span>
                    <span class="dot">·</span>
                    <span>workbook no longer on disk</span>
                    <span class="dot">·</span>
                    <span>{html.escape(size_label)}</span>
                    <span class="dot">·</span>
                    <span>{html.escape(time_label)}</span>
                </div>
            </div>
            <div class="folder-actions">
                <a class="button-link secondary" href="/download-audit/{html.escape(audit_path.name)}">Download audit</a>
            </div>
        </div>
        """

    # ---- Build body ----
    if not date_groups:
        outputs_html = """
        <div class="empty-state">
            <h3 style="margin-bottom:8px;">No outputs yet</h3>
            <p style="margin:0;">Generate a workbook from the Home page and it will appear here.</p>
        </div>
        """
    else:
        sections = []
        for grp_date, grp_items in date_groups:
            primary, secondary = date_labels(grp_date)
            secondary_html = (
                f'<span class="date-meta">{html.escape(secondary)}</span>'
                if secondary else ""
            )
            item_word = "item" if len(grp_items) == 1 else "items"
            divider = f"""
            <div class="date-divider">
                <span class="date-label">{html.escape(primary)}</span>
                {secondary_html}
                <span class="date-count">{len(grp_items)} {item_word}</span>
            </div>
            """
            cards = []
            for it in grp_items:
                if it["kind"] == "batch":
                    cards.append(render_batch(it))
                elif it["kind"] == "single":
                    cards.append(render_single(it))
                else:
                    cards.append(render_audit_only(it))
            sections.append(divider + "".join(cards))
        outputs_html = '<div class="outputs-list">' + "".join(sections) + "</div>"

    page = """
<!doctype html>
<html>
__HEAD__
<body>
<div class="shell">
    __TOPBAR__
    __HERO__

    <div class="card">
        <h2>Completed Workbooks &amp; Audits</h2>
        <p class="muted">Batches are shown as folders containing each generated workbook. Single runs appear as individual cards. Everything is grouped by the day it was produced.</p>
        __OUTPUTS_HTML__
    </div>
</div>
</body>
</html>
    """

    page = page.replace("__HEAD__", head_html("Outputs | Phillip Capital Risk Management"))
    page = page.replace("__TOPBAR__", topbar_html("outputs", user))
    page = page.replace(
        "__HERO__",
        hero_html(
            "Completed Outputs",
            "View and download generated Excel workbooks, batch ZIP files, and audit reports.",
        ),
    )
    page = page.replace("__OUTPUTS_HTML__", outputs_html)

    return page


# ============================================================
# BATCH WORKER (live progress)
# ============================================================

