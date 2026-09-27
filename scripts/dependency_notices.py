"""Record installed distribution metadata; retain upstream license files in dependencies."""

import importlib.metadata as metadata
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
records = []
for dist in metadata.distributions():
    m = dist.metadata
    records.append(
        dict(
            name=m.get("Name"),
            version=dist.version,
            license=m.get("License-Expression")
            or m.get("License")
            or "; ".join(
                x for x in m.get_all("Classifier", []) if x.startswith("License ::")
            ),
            author=m.get("Author") or m.get("Author-email"),
            urls=m.get_all("Project-URL", []),
            license_files=[
                str(p)
                for p in dist.files or []
                if "license" in str(p).lower() or "copying" in str(p).lower()
            ],
        )
    )
(root / "docs/DEPENDENCY_LICENSES.json").write_text(
    json.dumps(sorted(records, key=lambda x: x["name"].lower()), indent=2)
)
node_records = []
lock = json.loads((root / "frontend/package-lock.json").read_text())
for package, entry in lock["packages"].items():
    if not package:
        continue
    node_records.append(
        dict(
            package=package,
            version=entry["version"],
            license=entry.get("license", "See installed package license"),
            source=entry.get("resolved"),
        )
    )
(root / "docs/FRONTEND_LICENSES.json").write_text(json.dumps(node_records, indent=2))
print(
    f"Recorded {len(records)} Python and {len(node_records)} frontend package notices."
)
