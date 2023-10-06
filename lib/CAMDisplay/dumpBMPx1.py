def extract_bmp_1(input_file_path, output_python_file):
    # Open the BMP file in binary mode for reading
    with open(input_file_path, 'rb') as bmp_file:
        # Read the width and height from the BMP file header
        bmp_file.seek(18)  # Skip to the width bytes in the header
        width = int.from_bytes(bmp_file.read(4), 'little')
        height = int.from_bytes(bmp_file.read(4), 'little')

        # Calculate the number of bytes needed to store the image data
        image_data_size = (width // 8) * height

        # Read the image data
        bmp_file.seek(62)  # Skip to the start of pixel data
        image_data = bmp_file.read(image_data_size)

    # Create a formatted string for the image data
    formatted_image_data = ""
    for i in range(len(image_data), 0, -16):
        formatted_image_data += "b'\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}\\x{:02x}' + \\\n".format(image_data[i-16], image_data[i-15], image_data[i-14], image_data[i-13], image_data[i-12], image_data[i-11], image_data[i-10], image_data[i-9], image_data[i-8], image_data[i-7], image_data[i-6], image_data[i-5], image_data[i-4], image_data[i-3], image_data[i-2], image_data[i-1])

    # Save the image data as a formatted bytearray in a Python file
    with open(output_python_file, 'w') as python_file:
        python_file.write(f'width = {width}\n')
        python_file.write(f'height = {height}\n')
        python_file.write('image_data = (')
        python_file.write(formatted_image_data)
        python_file.write('\n)\n')

    print(f"Image dimensions: {width} x {height}")

# Specify the input BMP file and the output Python file
#input_bmp_file = 'bmp1.bmp'
#output_python_file = 'img.py'

# Call the function to extract and save the image data
#extract_bmp_1(input_bmp_file, output_python_file)