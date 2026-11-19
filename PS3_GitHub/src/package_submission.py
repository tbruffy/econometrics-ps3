"""Create clean upload archives after analysis and LaTeX compilation."""
from pathlib import Path
import zipfile
import os

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent
overleaf = [ROOT / "main.tex", ROOT / "config.tex"]
overleaf += sorted((ROOT / "sections").glob("*.tex"))
overleaf += sorted((ROOT / "tables").glob("*.tex"))
overleaf += sorted((ROOT / "figures").glob("*.pdf"))
assert (ROOT / "submission/PS3_Travis_Bruffy.pdf").is_file(), "Compile PDF first."
assert len(list((ROOT / "sections").glob("problem*.tex"))) == 6

portable = []
for base, directories, filenames in os.walk(ROOT):
    directories[:] = sorted(d for d in directories
                             if d not in {".venv", "__pycache__", ".review", ".git", "tools"})
    for filename in filenames:
        path = Path(base) / filename
        if path.suffix in {".aux", ".log", ".out", ".zip", ".pyc", ".synctex"}:
            continue
        if path.name in {"main.pdf", ".DS_Store"}:
            continue
        portable.append(path)
for name, files in [("PS3_Overleaf.zip", overleaf), ("PS3_GitHub.zip", sorted(portable))]:
    target = DEST / name
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert "main.tex" in archive.namelist()
        print(f"{name}: {len(archive.namelist())} files, {target.stat().st_size:,} bytes")
