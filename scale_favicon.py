#!/usr/bin/env python3
"""
Scale up the favicon while keeping the whole logo visible
"""
from PIL import Image

def scale_up_favicon():
    """Scale up fav.png to make the logo bigger"""
    input_file = 'fav.png'
    output_file = 'favicon.png'
    
    # Open the image
    img = Image.open(input_file)
    original_width, original_height = img.size
    print(f"Original size: {original_width}x{original_height}")
    
    # Scale up by 40% (1.4x) - a little bigger
    scale_factor = 1.4
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # Resize with high-quality resampling
    scaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"Scaled up to: {new_width}x{new_height}")
    
    # Save
    scaled.save(output_file, 'PNG', optimize=True)
    print(f"✅ Saved larger favicon!")
    print(f"   The logo is now 20% bigger while keeping the whole logo visible")

if __name__ == '__main__':
    scale_up_favicon()

