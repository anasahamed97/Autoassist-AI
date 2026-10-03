"""
Utility script to generate an authentic multi-page PDF automotive service manual
using native Python PDF 1.4 stream formatting, with zero external dependencies.
"""
from pathlib import Path


def create_minimal_pdf(pages_text: list[str], output_path: Path):
    """Generates a valid multi-page PDF document containing text on each page."""
    objects = []
    
    # Object 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    
    # We will build pages and content streams
    num_pages = len(pages_text)
    page_obj_ids = [3 + i * 2 for i in range(num_pages)]
    content_obj_ids = [4 + i * 2 for i in range(num_pages)]
    
    # Object 2: Pages container
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode("ascii"))
    
    # Font Object
    font_id = 3 + num_pages * 2
    font_obj = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    
    for i, text in enumerate(pages_text):
        # Escape parenthesis in text
        escaped_lines = []
        for line in text.split("\n"):
            clean_l = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            escaped_lines.append(clean_l)
        
        # Build PDF text stream
        stream_cmds = ["BT", f"/F1 12 Tf", "50 750 Td", "14 TL"]
        for line in escaped_lines:
            stream_cmds.append(f"({line}) '")
        stream_cmds.append("ET")
        stream_data = "\n".join(stream_cmds).encode("latin1", errors="replace")
        
        # Page object
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_obj_ids[i]} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        ).encode("ascii")
        objects.append(page_obj)
        
        # Content stream object
        content_stream_obj = (
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
            + stream_data
            + b"\nendstream"
        )
        objects.append(content_stream_obj)
        
    objects.append(font_obj)
    
    # Write PDF file
    with open(output_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        offsets = []
        for idx, obj in enumerate(objects, start=1):
            offsets.append(f.tell())
            f.write(f"{idx} 0 obj\n".encode("ascii"))
            f.write(obj)
            f.write(b"\nendobj\n")
            
        xref_offset = f.tell()
        f.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        f.write(b"0000000000 65535 f \n")
        for offset in offsets:
            f.write(f"{offset:010d} 00000 n \n".encode("ascii"))
            
        f.write(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )
    print(f"Generated PDF with {num_pages} pages at: {output_path}")


if __name__ == "__main__":
    pages = [
        # Page 1
        "HONDA CIVIC WORKSHOP SERVICE & REPAIR MANUAL\n"
        "Model: Honda Civic 1.5L Turbo / 2.0L\n"
        "Model Year: 2022\n"
        "Document Type: Workshop Manual\n"
        "Source: American Honda Motor Technical Information\n\n"
        "SECTION 1: GENERAL MAINTENANCE & FLUID SPECIFICATIONS\n\n"
        "Engine Oil Capacity: 3.5 Liters with filter replacement.\n"
        "Recommended Viscosity: Genuine Honda 0W-20 Full Synthetic Motor Oil.\n"
        "Coolant Specification: Honda Long Life Antifreeze / Coolant Type 2 (pre-mixed 50/50).\n"
        "Brake Fluid: Genuine Honda Heavy Duty Brake Fluid DOT 3.",

        # Page 2
        "SECTION 2: COOLING SYSTEM DIAGNOSIS & BLEEDING\n\n"
        "Engine Overheating Troubleshooting:\n"
        "1. Check coolant reserve tank level when cold. If below MIN line, inspect for leaks.\n"
        "2. If temperature gauge needle reaches H (Hot), turn off A/C and safely stop engine.\n"
        "3. Radiator Fan Operation: Ensure both radiator fan and condenser fan activate when\n"
        "   engine coolant temperature reaches 199 deg F (93 deg C).\n"
        "4. Bleeding Air from Cooling System: Fill reserve tank to MAX. Loosen bleed bolt if\n"
        "   equipped until coolant flows without air bubbles, then tighten to 7.2 lb-ft (10 N-m).",

        # Page 3
        "SECTION 3: STARTING SYSTEM & 12V BATTERY TESTING\n\n"
        "Starting Symptom: Clicking Noise / No Engine Crank\n"
        "- If starter solenoid clicks rapidly, 12V battery terminal voltage is below 10.0V.\n"
        "- Clean corroded battery posts with sodium bicarbonate solution and wire brush.\n"
        "- Parasitic Draw Inspection: Standard quiescent current must be under 35mA after\n"
        "  security system arms and BCM enters sleep mode (allow 20 minutes).\n"
        "- Starter Relay Check: Swap starter cut relay with horn relay in engine under-hood box.",

        # Page 4
        "SECTION 4: BRAKE SYSTEM WEAR LIMITS & INSPECTION\n\n"
        "Brake Pad Thickness Specification:\n"
        "- Front Brake Pad Standard Thickness: 9.5 mm to 10.5 mm.\n"
        "- Service Wear Limit: 1.6 mm (replace pads immediately if below 2.0 mm).\n"
        "- Brake Rotor Thickness Standard: 25.0 mm. Minimum Refinish Limit: 23.0 mm.\n"
        "- Brake Squeak / Squeal Cause: Wear indicators contact rotor when pad thickness\n"
        "  drops below 2.5 mm. Replace front pad set and lubricate caliper sliding pins."
    ]

    out_file = Path("data/raw/honda_civic_service_and_maintenance.pdf")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    create_minimal_pdf(pages, out_file)
