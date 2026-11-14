# 📦 ArchiveKit

A small ZIP/TAR command-line utility built entirely with Python's standard library.

## Examples

```bash
python archivekit.py list project.zip
python archivekit.py test project.zip
python archivekit.py create ./project project.zip
python archivekit.py create ./project project.tar.gz --format tar.gz
python archivekit.py extract project.zip ./output
```

Supports ZIP, TAR and TAR.GZ. Extraction rejects parent-traversal paths and TAR links. It does not require `pip install` or any external executable.

Requires Python 3.9+.
