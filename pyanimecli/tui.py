import os, time, shutil, sys
from functools import lru_cache
try:
    from PIL import Image
    import numpy as np
except ImportError:
    import subprocess as sp
    res = sp.run([sys.executable, "-m", "pip", "install", "pillow", "numpy", "--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org"])
    from PIL import Image
    import numpy as np

def RGB_to_ANSI(fg_r, fg_g, fg_b, bg_r=None, bg_g=None, bg_b=None):
    """
    Converts RGB values to ANSI escape sequences.
    - `fg_r, fg_g, fg_b`: Foreground RGB color
    - `bg_r, bg_g, bg_b`: (Optional) Background RGB color
    Returns an ANSI escape string for colored text rendering.
    """
    fg_code = f"\033[38;2;{fg_r};{fg_g};{fg_b}m"  # Set foreground color
    bg_code = f"\033[48;2;{bg_r};{bg_g};{bg_b}m" if bg_r is not None else ""  # Set background (if provided)
    return fg_code + bg_code  # Combine codes

@lru_cache(maxsize=None)
def get_cached_ansi(fg_r, fg_g, fg_b, bg_r, bg_g, bg_b):
    return RGB_to_ANSI(fg_r, fg_g, fg_b, bg_r, bg_g, bg_b)


def render_frame(frame):
    if isinstance(frame, np.ndarray):
        data = frame
    else:
        data = np.array(frame, dtype=np.uint8)  # shape (height*2, width, 3)
    top = data[0::2]         # every other row starting at 0
    bottom = data[1::2]      # every other row starting at 1
    output_lines = ["\033[H"]
    for top_row, bottom_row in zip(top, bottom):
        line_chars = []
        previous_ansi = None
        for (r, g, b), (br, bg, bb) in zip(top_row, bottom_row):
            ansi = get_cached_ansi(int(r), int(g), int(b), int(br), int(bg), int(bb))
            if ansi == previous_ansi:
                line_chars[-1]  += "▀"
            else:
                line_chars.append(ansi + "▀")
                previous_ansi = ansi
        output_lines.append("".join(line_chars))
    output_lines.append("\033[0m")
    return "\n".join(output_lines)


def main(image_path=None, image=None):
    img = image or Image.open(image_path)

    ANIMATED = False
    if hasattr(img, "is_animated") and img.is_animated:
        ANIMATED = True

    width, height = shutil.get_terminal_size()
    height -= 1
    width -= 1
    size = (width, height * 2)

    if ANIMATED:
        frames = []
        while True:
            try:
                frames.append(img.copy())
                img.seek(img.tell() + 1)
            except EOFError:
                break
        
        frames = [frame.resize(size).convert("RGB") for frame in frames]
        rendered_frames = [render_frame(frame) for frame in frames]

        while True:
            for frame in rendered_frames:
                sys.stdout.write(frame)
                sys.stdout.flush()
                # time.sleep(frame.info['duration'] / 1000)
                # Removed to improve performance (terminal write delay already provides a significant delay between frames)
    else:
        frame = img.resize(size).convert("RGB")
        sys.stdout.write(render_frame(frame))
        sys.stdout.flush()


if __name__ == "__main__":
    # IMAGE_NAME = "OIP.jfif"
    IMAGE_NAME = "rickroll.gif"
    main(os.path.join(os.path.dirname(__file__), IMAGE_NAME))