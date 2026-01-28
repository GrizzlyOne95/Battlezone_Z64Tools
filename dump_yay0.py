import os

def extract_assets(rom_path, output_dir="extracted_assets"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Known N64 magic numbers/headers
    # MIO0: Compression, Yay0: Compression, AIFF/VAD: Audio, PNG/BMP: Rare but possible
    magic_numbers = {
        b'MIO0': '.mio0',
        b'Yay0': '.yay0',
        b'Yaz0': '.yaz0',
        b'FORM': '.aiff', # Often used for audio containers
    }

    with open(rom_path, "rb") as f:
        data = f.read()
        print(f"Loaded {rom_path} ({len(data)} bytes)")

        for magic, ext in magic_numbers.items():
            start_pos = 0
            count = 0
            while True:
                start_pos = data.find(magic, start_pos)
                if start_pos == -1:
                    break
                
                # Attempt to determine size or just extract a chunk
                # Note: This is a simplified 'carve'. In N64, sizes are often 
                # stored in the 4 bytes immediately following the magic.
                filename = os.path.join(output_dir, f"asset_{start_pos:08X}{ext}")
                
                # Basic carving: grab 0x10000 bytes or use header logic
                # For MIO0, the decompressed size is at offset 4
                extract_size = 0x20000 # Default fallback
                
                with open(filename, "wb") as out:
                    out.write(data[start_pos : start_pos + extract_size])
                
                print(f"Found {magic.decode()} at {hex(start_pos)}, saved to {filename}")
                start_pos += 4
                count += 1
            print(f"Extracted {count} files of type {ext}")

if __name__ == "__main__":
    extract_assets("rotbd.z64")