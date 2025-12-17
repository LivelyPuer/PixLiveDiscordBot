from PIL import Image, ImageFilter
import io

def blur_image(image_bytes: bytes, radius: int = 40) -> bytes:
    """
    Applies Gaussian blur to an image.
    
    Args:
        image_bytes: The input image data in bytes.
        radius: The radius of the blur.
        
    Returns:
        bytes: The blurred image data in JPEG format.
    """
    if not image_bytes:
        return image_bytes

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert to RGB to handle PNGs with transparency or other modes
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            blurred = img.filter(ImageFilter.GaussianBlur(radius))
            
            output = io.BytesIO()
            blurred.save(output, format='JPEG', quality=85)
            return output.getvalue()
    except Exception as e:
        # If blurring fails, return original or re-raise? 
        # For safety/simplicity, logging error and returning original might be risky if it was NSFW.
        # But failing hard is better than leaking NSFW.
        # Let's re-raise or return empty.
        print(f"Error blurring image: {e}")
        raise e
