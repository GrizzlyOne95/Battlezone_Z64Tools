import os
from PIL import Image

def save_as_png(data, width, filename, mode='RGBA'):
    # N64 RGBA16 (5551) to Standard RGBA
    if len(data) < width * 2: return
    
    height = len(data) // (width * 2)
    img = Image.new('RGBA', (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 2
            if idx + 1 >= len(data): break
            
            # Read 16-bit pixel
            pixel = (data[idx] << 8) | data[idx+1]
            
            # Convert 5551 to 8888
            r = ((pixel >> 11) & 0x1F) << 3
            g = ((pixel >> 6) & 0x1F) << 3
            b = ((pixel >> 1) & 0x1F) << 3
            a = 255 if (pixel & 1) else 0
            pixels[x, y] = (r, g, b, a)
            
    img.save(filename)

def mass_convert(input_dir):
    out_dir = "texture_previews"
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".bin"):
            with open(os.path.join(input_dir, filename), "rb") as f:
                data = f.read()
                
            # Try common N64 widths
            for w in [32, 64, 128]:
                # Only attempt if the data size makes sense for this width
                if len(data) % (w * 2) == 0 and len(data) > 0:
                    out_name = os.path.join(out_dir, f"{filename}_w{w}.png")
                    save_as_png(data, w, out_name)

if __name__ == "__main__":
    # You'll need to install Pillow: pip install Pillow
    mass_convert("decompressed_assets")