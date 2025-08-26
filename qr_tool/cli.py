import base64
import math
import struct
import zlib
from pathlib import Path
from typing import List
from qreader import QReader

import cv2
import qrcode
import typer

app = typer.Typer(help="Encode and decode files to/from QR codes.")

# Maximum payload per QR code chunk (bytes). Conservatively below theoretical limit.
CHUNK_SIZE = 2200  # binary bytes per chunk before base64 encoding


def _maybe_compress(data: bytes) -> tuple[bytes, bool]:
    """Compress data with zlib if it results in a smaller payload."""
    compressed = zlib.compress(data)
    if len(compressed) < len(data):
        return compressed, True
    return data, False


@app.command()
def encode(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output_dir: Path = typer.Option(Path("qr_output"), help="Directory to write QR images."),
    display: bool = typer.Option(True, help="Display each QR code for scanning."),
) -> None:
    """Encode FILE into a sequence of QR codes."""
    data = file.read_bytes()
    payload, compressed = _maybe_compress(data)

    name_bytes = file.name.encode("utf-8")
    meta = len(name_bytes).to_bytes(2, "big") + name_bytes + (b"\x01" if compressed else b"\x00")
    payload = meta + payload

    total_chunks = math.ceil(len(payload) / CHUNK_SIZE)
    output_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Encoding {len(data)} bytes into {total_chunks} QR codes...")

    for idx in range(total_chunks):
        chunk = payload[idx * CHUNK_SIZE : (idx + 1) * CHUNK_SIZE]
        header = struct.pack(">HH", idx, total_chunks)
        b64 = base64.b64encode(header + chunk).decode("ascii")
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(b64)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_path = output_dir / f"{file.stem}_{idx:04d}.png"
        img.save(img_path)
        typer.echo(f"Saved {img_path}")
        if display:
            img.show()
            if idx + 1 < total_chunks:
                typer.prompt("Scan this code and press Enter for next", default="", prompt_suffix="")


@app.command()
def decode(
    images: List[Path] = typer.Argument(
        ..., exists=True, readable=True, dir_okay=True
    ),
    output: Path | None = typer.Option(None, help="Output file path."),
) -> None:
    """Decode QR code images back into the original file."""
    chunks: dict[int, bytes] = {}
    total_expected: int | None = None

    # Gather all image paths, expanding directories.
    image_paths: List[Path] = []
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"}
    for p in images:
        if p.is_dir():
            for ext in exts:
                image_paths.extend(sorted(p.glob(f"*{ext}")))
        else:
            image_paths.append(p)

    qreader = QReader()
    if not image_paths:
        raise typer.BadParameter("No image files provided")

    for path in sorted(image_paths):
        img = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)
        if img is None:
            raise typer.BadParameter(f"Could not read {path}")
        data = qreader.detect_and_decode(image=img)[0]
        raw = base64.b64decode(data.encode("ascii"))
        idx, total = struct.unpack(">HH", raw[:4])
        chunk = raw[4:]
        chunks[idx] = chunk
        total_expected = total_expected or total
        if total_expected != total:
            raise typer.BadParameter("Mismatched total chunks in QR codes")

    if total_expected is None or len(chunks) != total_expected:
        raise typer.BadParameter("Missing QR chunks; expected complete sequence")

    payload = b"".join(chunks[i] for i in range(total_expected))
    name_len = int.from_bytes(payload[:2], "big")
    name_end = 2 + name_len
    name = payload[2:name_end].decode("utf-8")
    compressed_flag = payload[name_end]
    file_data = payload[name_end + 1 :]
    if compressed_flag:
        file_data = zlib.decompress(file_data)

    out_path = output or Path(name)
    out_path.write_bytes(file_data)
    typer.echo(f"Wrote {out_path} ({len(file_data)} bytes)")


if __name__ == "__main__":
    app()
