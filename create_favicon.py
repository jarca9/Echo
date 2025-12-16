#!/usr/bin/env python3
"""
Create a zoomed-out favicon by scaling down the image and adding padding
"""
from PIL import Image
import os

def create_zoomed_out_favicon():
    """Zoom out by scaling down the image and adding padding"""
    input_file = 'favicon_original.png' if os.path.exists('favicon_original.png') else 'favicon.png'
    output_file = 'favicon.png'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return
    
    # Open the original image
    img = Image.open(input_file)
    width, height = img.size
    print(f"Original size: {width}x{height}")
    
    # Zoom out: Scale down to 85% and add padding
    scale_factor = 0.85
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Resize the image (this makes everything smaller)
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"Scaled down to: {new_width}x{new_height}")
    
    # Create a new 500x500 canvas with transparent background
    new_img = Image.new('RGBA', (500, 500), (0, 0, 0, 0))
    
    # Calculate position to center the scaled image
    x_offset = (500 - new_width) // 2
    y_offset = (500 - new_height) // 2
    
    # Paste the scaled image onto the center of the new canvas
    new_img.paste(resized, (x_offset, y_offset), resized if resized.mode == 'RGBA' else None)
    print(f"Pasted onto 500x500 canvas with padding")
    
    # Save
    new_img.save(output_file, 'PNG', optimize=True)
    print(f"✅ Saved zoomed-out favicon!")
    print(f"   The logo should now appear smaller with more space around it")

if __name__ == '__main__':
    create_zoomed_out_favicon()
