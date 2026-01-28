import os
import struct

def decompress_yay0(data):
    # Yay0 Header: Magic[4], DecSize[4], LinkPtr[4], NonLinkPtr[4]
    if data[:4] != b'Yay0':
        return None
    
    uncompressed_size = struct.unpack(">I", data[4:8])[0]
    link_offset = struct.unpack(">I", data[8:12])[0]
    non_link_offset = struct.unpack(">I", data[12:16])[0]
    
    output = bytearray()
    mask_bit_counter = 0
    current_mask = 0
    
    command_ptr = 16
    
    while len(output) < uncompressed_size:
        if mask_bit_counter == 0:
            current_mask = struct.unpack(">I", data[command_ptr:command_ptr+4])[0]
            command_ptr += 4
            mask_bit_counter = 32
        
        if (current_mask >> 31) & 1:
            # Copy 1 byte from non-link data
            output.append(data[non_link_offset])
            non_link_offset += 1
        else:
            # Copy N bytes from already decompressed data
            link = struct.unpack(">H", data[link_offset:link_offset+2])[0]
            link_offset += 2
            
            # Distance and Count
            dist = (link & 0xFFF) + 1
            count = link >> 12
            
            if count == 0:
                # Count is 0, so read extra byte for count
                count = data[non_link_offset] + 16
                non_link_offset += 1
            else:
                count += 2
                
            start_copy = len(output) - dist
            for i in range(count):
                output.append(output[start_copy + i])
        
        current_mask = (current_mask << 1) & 0xFFFFFFFF
        mask_bit_counter -= 1
        
    return output

def process_folder(input_dir):
    out_dir = "decompressed_assets"
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".yay0"):
            with open(os.path.join(input_dir, filename), "rb") as f:
                compressed_data = f.read()
            
            print(f"Decompressing {filename}...")
            try:
                decompressed = decompress_yay0(compressed_data)
                if decompressed:
                    with open(os.path.join(out_dir, filename.replace(".yay0", ".bin")), "wb") as f:
                        f.write(decompressed)
            except Exception as e:
                print(f"Failed to decompress {filename}: {e}")

if __name__ == "__main__":
    # Point this to the folder where your 984 YAY0 files are
    process_folder("extracted_assets")