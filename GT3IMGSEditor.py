import os
import struct
import sys
import re

# Custom sorting function for filenames
def custom_sort(filename):
    parts = re.split(r'(\d+)', filename)  # Split on digits
    return [s.lower() if not s.isdigit() else int(s) for s in parts]

def extract_images(archive_file):
    with open(archive_file, 'rb') as f:
        magic = f.read(4)
        if magic != b'IMGS':
            print("Invalid archive format.")
            return
        print("Archive Magic: IMGS")

        f.seek(8)
        file_count = struct.unpack('<I', f.read(4))[0]
        print("File Count:", file_count)

        # Search for Tex1 headers and calculate lengths
        tex1_offsets = []
        while True:
            tex1_offset = f.tell()  # Current position is a potential Tex1 start
            header = f.read(4)
            if not header:
                break  # Reached end of file
            if header == b'Tex1':
                tex1_offsets.append(tex1_offset)

        print("Found", len(tex1_offsets), "Tex1 files.")
        print("Tex1 Offsets:", tex1_offsets)

        # Read the filename & ID table
        filenames = []
        f.seek(16)  # Start of filename table
        for _ in range(file_count):
            name_bytes = f.read(60)
            filename = name_bytes.split(b'\x00', 1)[0].decode('utf-8')
            filenames.append(filename)
            f.seek(4, 1)  # Skip 4 bytes for the file ID

        # Create 'out' folder if it doesn't exist
        if not os.path.exists('out'):
            os.makedirs('out')

        # Iterate through Tex1 files and extract to 'out' folder
        for i, tex1_offset in enumerate(tex1_offsets):
            f.seek(tex1_offset + 4)  # Skip the "Tex1" header
            size_offset = tex1_offset + 12  # Calculate the size offset
            f.seek(size_offset)
            file_size = struct.unpack('<I', f.read(4))[0]

            # Read the filename
            if i < len(filenames):
                filename = filenames[i]
            else:
                filename = f"Tex1_File_{i + 1}.dat"  # Default filename if not found

            out_filename = os.path.join('out', filename)
            with open(out_filename, 'wb') as out_file:
                # Move to the start of the Tex1 file
                f.seek(tex1_offset)
                # Read and write the file data
                out_file.write(f.read(file_size))

            print(f"Extracted Tex1 File {i + 1} - Size: {file_size}, Filename: {filename}")

        print("Extraction complete. Extracted files are in the 'out' folder.")

def build_archive(folder):
    out_folder = os.path.join(folder, 'out')
    if not os.path.exists(out_folder):
        print("Error: 'out' folder does not exist.")
        return

    filenames = os.listdir(out_folder)
    file_count = len(filenames)

    # Sort filenames using the custom sorting function
    filenames.sort(key=custom_sort)

    with open('archive.imgs', 'wb') as f:
        # Placeholder for header offset
        f.write(b'IMGS')
        f.write(b'\x00' * 4)  # Placeholder for unused bytes
        f.write(struct.pack('<I', file_count))  # Number of files
        offset_pos = f.tell()
        f.write(struct.pack('<I', 0))  # Placeholder for offset to file data

        # Write the filename & ID table
        for i, filename in enumerate(filenames):
            name_bytes = filename.encode('utf-8')
            id_bytes = struct.pack('<I', i)
            f.write(name_bytes.ljust(60, b'\x00'))  # Pad to 60 bytes
            f.write(id_bytes)

        # Get the start of file data (after header and table)
        start_file_data = f.tell()

        # Copy the files from 'out' folder to archive
        for filename in filenames:
            file_path = os.path.join(out_folder, filename)
            with open(file_path, 'rb') as img_file:
                file_data = img_file.read()
                f.write(file_data)

        # Calculate the offset to file data
        offset_to_file_data = start_file_data - offset_pos  # No need to add 12 bytes for Tex1 header
        f.seek(offset_pos)
        f.write(struct.pack('<I', offset_to_file_data))  # Write the correct offset

        # Find the offset to the first Tex1 file
        if len(filenames) > 0:
            tex1_offset = start_file_data
            f.seek(12)  # Go to the correct position for the first Tex1 offset
            f.write(struct.pack('<I', tex1_offset))  # Write the correct offset

    print("Archive 'archive.imgs' created.")

def main():
    if len(sys.argv) == 1:
        # If no arguments are provided, build archive from current directory
        build_archive(os.getcwd())
        return

    if len(sys.argv) > 2:
        print("Invalid arguments.")
        print("Usage:")
        print("To build an archive: python GT3IMGSEditor.py folder")
        print("To extract an archive: python GT3IMGSEditor.py archive.imgs")
        return

    if sys.argv[1].endswith(".imgs"):
        extract_images(sys.argv[1])
    else:
        build_archive(sys.argv[1])

if __name__ == "__main__":
    main()
