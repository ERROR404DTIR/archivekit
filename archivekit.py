#!/usr/bin/env python3
"""ArchiveKit — inspect, test, create and safely extract ZIP/TAR archives."""
import argparse, sys, tarfile, zipfile
from pathlib import Path, PurePosixPath

def safe_member(name):
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and all(x not in ("..", "") for x in p.parts)

def inspect(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for x in z.infolist():
                print(f"{x.file_size:>12,}  {x.filename}")
            print(f"\n{len(z.infolist())} entries | ZIP")
    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as t:
            for x in t.getmembers():
                kind = "DIR " if x.isdir() else "FILE"
                print(f"{x.size:>12,}  {kind}  {x.name}")
            print(f"\n{len(t.getmembers())} entries | TAR")
    else:
        raise SystemExit("Unsupported or invalid archive (ZIP/TAR only).")

def test(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad: raise SystemExit(f"Corrupt member: {bad}")
    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as t:
            for m in t.getmembers():
                if not safe_member(m.name): raise SystemExit(f"Unsafe path: {m.name}")
                if m.issym() or m.islnk(): raise SystemExit(f"Link entry not accepted: {m.name}")
                if m.isfile():
                    f = t.extractfile(m)
                    if f:
                        while f.read(1024 * 1024): pass
    else:
        raise SystemExit("Unsupported archive.")
    print("Archive integrity check passed.")

def create(source, output, fmt):
    source = source.resolve()
    if not source.exists(): raise SystemExit(f"Not found: {source}")
    if fmt == "zip":
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            items = [source] if source.is_file() else sorted(source.rglob("*"))
            for p in items:
                if p.is_file():
                    arc = p.name if source.is_file() else p.relative_to(source.parent).as_posix()
                    z.write(p, arc)
    else:
        mode = "w:gz" if fmt == "tar.gz" else "w"
        with tarfile.open(output, mode) as t:
            t.add(source, arcname=source.name)
    print(f"Created: {output}")

def extract(path, destination):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if not safe_member(n): raise SystemExit(f"Unsafe path rejected: {n}")
            z.extractall(destination)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as t:
            members = t.getmembers()
            for m in members:
                if not safe_member(m.name) or not (m.isfile() or m.isdir()):
                    raise SystemExit(f"Unsafe or unsupported archive entry rejected: {m.name}")
            t.extractall(destination, members=members)
    else:
        raise SystemExit("Unsupported archive.")
    print(f"Extracted into: {destination}")

def main():
    p = argparse.ArgumentParser(description="ZIP/TAR utility using only Python's standard library.")
    s = p.add_subparsers(dest="cmd", required=True)
    for cmd in ("list", "test"):
        q=s.add_parser(cmd); q.add_argument("archive", type=Path)
    q=s.add_parser("create"); q.add_argument("source", type=Path); q.add_argument("output", type=Path)
    q.add_argument("--format", choices=("zip","tar","tar.gz"), default="zip")
    q=s.add_parser("extract"); q.add_argument("archive", type=Path); q.add_argument("destination", type=Path)
    a=p.parse_args()
    if a.cmd=="list": inspect(a.archive)
    elif a.cmd=="test": test(a.archive)
    elif a.cmd=="create": create(a.source,a.output,a.format)
    else: extract(a.archive,a.destination)

if __name__=="__main__":
    try: main()
    except (OSError, zipfile.BadZipFile, tarfile.TarError) as e:
        print(f"Error: {e}",file=sys.stderr); raise SystemExit(2)
