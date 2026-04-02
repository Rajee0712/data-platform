"""Generate HTML validation report from saved JSON results."""

import json
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger


def generate_html_report(
    results_dir: str = "data/validation",
    output_dir: str = "docs/validation",
) -> None:
    """Generate a combined HTML report from all validation JSON results."""
    results_path = Path(results_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_results = []
    for json_file in sorted(results_path.glob("*_results.json")):
        with open(json_file) as f:
            all_results.append((json_file.stem, json.load(f)))

    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    rows = ""
    for name, result in all_results:
        success = result.get("success", False)
        status = "✅ Passed" if success else "❌ Failed"
        expectations = result.get("results", [])
        passed = sum(1 for r in expectations if r.get("success"))
        total = len(expectations)
        pipeline_name = name.replace("_results", "").replace("_", " ").title()
        pipeline_id = name.replace(" ", "_")

        detail_rows = ""
        for exp in expectations:
            exp_success = exp.get("success", False)
            exp_type = exp.get("expectation_config", {}).get("type", "unknown")
            exp_kwargs = exp.get("expectation_config", {}).get("kwargs", {})
            column = exp_kwargs.get("column", exp_kwargs.get("column_list", ""))
            result_detail = exp.get("result", {})
            unexpected_count = result_detail.get("unexpected_count", "")
            unexpected_pct = result_detail.get("unexpected_percent", "")
            detail = ""
            if unexpected_count != "":
                detail = (
                    f"— {unexpected_count} unexpected ({unexpected_pct:.1f}%)"
                    if unexpected_pct
                    else f"— {unexpected_count} unexpected"
                )

            detail_rows += f"""
                <tr class="expectation-row">
                    <td class="exp-name">{"✅" if exp_success else "❌"} {exp_type.replace("expect_", "").replace("_", " ").title()}</td>
                    <td class="{"pass" if exp_success else "fail"} exp-col">{"Passed" if exp_success else "Failed"}</td>
                    <td class="exp-detail">column: <code>{column}</code> {detail}</td>
                </tr>"""

        rows += f"""
        <tr class="pipeline-row" onclick="toggle('{pipeline_id}')" style="cursor:pointer;">
            <td><strong>{"▶" if success else "▼"} {pipeline_name}</strong></td>
            <td class="{"pass" if success else "fail"}">{status}</td>
            <td>{passed}/{total} <span style="color:#999; font-size:0.8em">(click to expand)</span></td>
        </tr>
        <tr id="{pipeline_id}" class="detail-section" style="display:none;">
            <td colspan="3" style="padding:0;">
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:#2d3748; color:white;">
                            <th style="padding:8px 24px;">Expectation</th>
                            <th style="padding:8px;">Status</th>
                            <th style="padding:8px;">Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        {detail_rows}
                    </tbody>
                </table>
            </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Platform — Validation Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; color: #333; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #1a1a2e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
        .pipeline-row td {{ background: #f0f4f8; font-size: 1.05em; border-top: 2px solid #1a1a2e; }}
        .pipeline-row:hover td {{ background: #e2e8f0; }}
        .expectation-row td {{ font-size: 0.9em; padding-left: 24px; }}
        .exp-col {{ font-size: 0.85em; }}
        .exp-detail {{ color: #666; }}
        code {{ background: #f0f0f0; padding: 1px 6px; border-radius: 3px; font-size: 0.85em; }}
        .pass {{ color: #4CAF50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
    </style>
    <script>
        function toggle(id) {{
            const row = document.getElementById(id);
            row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
        }}
    </script>
</head>
<body>
    <h1>🌍 Data Platform — Validation Report</h1>
    <p class="timestamp">Generated: {timestamp}</p>
    <table>
        <thead>
            <tr>
                <th>Pipeline</th>
                <th>Status</th>
                <th>Expectations</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""

    report_path = output_path / "index.html"
    with open(report_path, "w") as f:
        f.write(html)
    logger.info(f"HTML report generated at {report_path}")


if __name__ == "__main__":
    generate_html_report()
