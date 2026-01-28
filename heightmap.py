import os
import struct
from PIL import Image

def extract_deinterlaced_map(bin_file, width=64, height=64, offset=0x40):
    with open(bin_file, "rb") as f:
        f.seek(offset)
        
        pixels = []
        # We assume each row of 64 heights is followed by 64 units of other data
        # So we read (width * 2) bytes, then skip (width * 2) bytes
        row_size_bytes = width * 2
        
        for r in range(height):
            # Read the actual height row
            row_data = f.read(row_size_bytes)
            if len(row_data) < row_size_bytes: break
            
            for i in range(0, len(row_data), 2):
                val = struct.unpack(">H", row_data[i:i+2])[0]
                pixels.append(val >> 8) # Convert to 8-bit grayscale
            
            # SKIP the next row of interleaved data
            f.seek(row_size_bytes, 1) # '1' means relative to current position

    if len(pixels) < width * height:
        print(f"Not enough data for {width}x{height} at offset {hex(offset)}")
        return

    img = Image.new('L', (width, height))
    img.putdata(pixels[:width*height])
    img = img.resize((512, 512), Image.NEAREST)
    
    out_name = f"DEINTERLACED_{width}_{os.path.basename(bin_file)}.png"
    img.save(out_name)
    print(f"Saved: {out_name}")

if __name__ == "__main__":
    path = r"C:\Users\istuart\Downloads\decompressed_assets\asset_00949B3C.bin"
    # Testing the 0x40 offset which looked most promising in your upload
    extract_deinterlaced_map(path, width=64, height=64, offset=0x40)