# qr

CLI tool to convert files to and from sequences of QR codes.

## Usage

### Encode a file into QR codes

```bash
uv run qr encode archive.zip --output-dir qrs
```

This command splits `archive.zip` into multiple QR images stored in `qrs/` and
opens an interactive viewer so they can be scanned. Press Enter or the right
arrow to advance to the next code, or the left arrow to go back.

### Decode QR codes back into a file

```bash
uv run qr decode qrs/ --output restored.zip
```

You can pass individual image paths or a directory containing the images. The
images are read, ordered automatically, and the original file is restored.
The decoder is tolerant of typical phone camera photos where the QR code does
not perfectly fill the frame. If `--output` is omitted, the original filename
embedded in the QR data is used.
