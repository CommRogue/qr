# qr

CLI tool to convert files to and from sequences of QR codes.

## Usage

### Encode a file into QR codes

```bash
uv run qr encode archive.zip --output-dir qrs
```

This command splits `archive.zip` into multiple QR images stored in `qrs/` and
shows each image sequentially so it can be scanned.

### Decode QR codes back into a file

```bash
uv run qr decode qrs/archive_*.png --output restored.zip
```

The images are read, ordered automatically, and the original file is restored.
If `--output` is omitted, the original filename embedded in the QR data is used.
