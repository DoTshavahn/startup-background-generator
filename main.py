# -*- coding: utf-8 -*-
""" *==LICENSE==*
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

The Cyan Worlds logo contained in this repository is not part of the GPL licensed content, and is copyrighted by Cyan
Worlds, Inc.
 *==LICENSE==* """

import argparse
import logging
from PIL import Image, ImageOps, ImageDraw, ImageFont
from matplotlib import font_manager


# Constants
CYAN_LOGO_FILE = (
    "cyan_logo.png"  # The filename containing the Cyan logo to add to the background.
)
CANVAS_SIZE = (
    3840,
    1080,
)  # The size of the image canvas before being scaled for the final texture size.
TEXTURE_SIZE = (
    4096,
    1080,
)  # The size of the image canvas before being scaled for the final texture size.
DIALOG_HEIGHT_PERCENT = (
    66  # The 'Explorers' dialog renders with the height as 66% of the screen height.
)
DIALOG_WIDTH_RATIO = (
    0.75  # The 'Explorers' dialog has a width that is 75% of its height.
)
DIALOG_AREA_COLOR = (
    128,
    0,
    0,
    64,
)  # In diagnostics mode, render the dialog zone as a transparent red.
ZONE_BORDER_SIZE = (
    10  # In diagnostics mode, render the aspect ratio safe zones with a 10px border.
)

# Structure containing aspect ratios to show as safe zones in the diagnostic image.
ASPECT_RATIOS = {
    "32:9": {"width": 32, "height": 9, "diag_color": (0, 128, 0, 64)},
    "21:9": {"width": 21, "height": 9, "diag_color": (128, 128, 0, 64)},
    "16:9": {"width": 16, "height": 9, "diag_color": (0, 128, 128, 64)},
    "4:3": {"width": 4, "height": 3, "diag_color": (128, 0, 128, 64)},
}


def draw_diagnostic_text(image, text):
    """Draws diagnostic text on the diagnostic image.

    Args:
        image: The PIL.Image object to draw the text on.
        text: The diagnostic text to write to the Image.
    """

    # Use Mathplotlib's font manager to find a sensible font on the system
    font = font_manager.FontProperties(family="monospace", weight="bold")
    font_file = font_manager.findfont(font)

    # Use the selected font and write draw the text to the image.
    fnt = ImageFont.truetype(font_file, 18)
    d = ImageDraw.Draw(image)
    d.text((10, 10), text, font=fnt)


def draw_dialog_zone(working_canvas):
    """Draws a solid rectangle on the diagnostic image showing the area covered by the 'Explorers' dialog.

    Args:
        working_canvas: The global PIL.Image canvas to draw the dialog rectangle onto.
    """

    # Calculate the dimensions of the dialog.
    dialog_height = round((working_canvas.height / 100) * DIALOG_HEIGHT_PERCENT)
    dialog_width = round(dialog_height * DIALOG_WIDTH_RATIO)

    # Create an image representing the area the 'Explorer' dialog will cover.
    dialog_area = Image.new(
        mode="RGBA", size=(dialog_width, dialog_height), color=DIALOG_AREA_COLOR
    )

    # Place the explanatory text on the zone
    draw_diagnostic_text(dialog_area, "[Explorers dialog area]")

    # Calculate the coordinates to place the dialog area in the center of the screen
    h_offset = round((working_canvas.width / 2) - (dialog_area.width / 2))
    v_offset = round((working_canvas.height / 2) - (dialog_area.height / 2))

    # Place the image in the center of the canvas
    working_canvas.paste(dialog_area, (h_offset, v_offset), dialog_area)


def draw_aspect_ratio_zone(working_canvas, ratio_name, ratio_specs):
    """Draws a rectangular border on the diagnostic image representing the area seen in the given aspect ratio.

    Args:
        working_canvas: The global PIL.Image canvas to draw the safe zone rectangle onto.
        ratio_name: The name of the aspect ratio.
        ratio_specs: Specs about the aspect ratio used to draw the rectangle and text.

    """

    # Calculate the real size of the area covered by the ratio
    zone_height = working_canvas.height
    zone_width = round(
        (working_canvas.height / ratio_specs["height"]) * ratio_specs["width"]
    )

    # Create a transparent image to represent the zone slightly smaller than the  final size
    ratio_area = Image.new(
        mode="RGBA",
        size=(
            zone_width - (ZONE_BORDER_SIZE * 2),
            zone_height - (ZONE_BORDER_SIZE * 2),
        ),
        color=(0, 0, 0, 0),
    )

    # Expand the transparent image to the final size, adding in our border zone color
    ratio_area = ImageOps.expand(
        ratio_area, border=ZONE_BORDER_SIZE, fill=ratio_specs["diag_color"]
    )

    # Calculate the horizontal offset needed to center the area
    h_offset = round((working_canvas.width / 2) - (ratio_area.width / 2))

    # Place the diagnostic text
    draw_diagnostic_text(ratio_area, f"[{ratio_name} safe zone]")

    # Place the image on the canvas
    working_canvas.paste(ratio_area, (h_offset, 0), ratio_area)


def percent_to_pixels(working_canvas, percent, mode="horizontal"):
    """Converts from a percent value to pixel value for item padding calculations.

    This function is used to convert a percentage value (e.g., 5%) to a pixel value (20). It is used so that we can
    pad logo elements from screen edges using percentage values rather than pixel values. This function can be used to
    calculate horizontal and vertical percentages, as those differ in non-square aspect ratios.

    Args:
        working_canvas: The global PIL.Image canvas. Used to calculate the percentage->pixel ratios.
        percent: The percent to convert into a pixel value.
        mode: Either 'horizontal' or 'vertical'. The reference frame for the calculation.

    Returns:
        The pixel value that represents that percentage of either horizontal or vertical screen space.
    """

    if mode not in ("horizontal", "vertical"):
        mode = "horizontal"

    if mode == "horizontal":
        return round((working_canvas.width / 100) * percent)
    elif mode == "vertical":
        return round((working_canvas.height / 100) * percent)


def draw_canvas_background(working_canvas, image_filename):
    """Places the given background image into the background of our canvas.

    The background image will fill the canvas area, maintaining it's original aspect ration. This means that if the
    image aspect ratio differs from our canvas ratio, the image's size will be cut off.

    Args:
        working_canvas: The global PIL.Image canvas to draw the background onto.
        image_filename: The filename of the image to use as our background.
    """

    # Load the background image
    background_image = Image.open(image_filename)

    # Scale the image to fill the background, maintaining its aspect ratio
    background_image = ImageOps.fit(
        background_image, working_canvas.size, centering=(0.5, 0.5)
    )

    # Place the image onto the canvas
    working_canvas.paste(background_image, (0, 0), background_image)


def draw_logo_element(
    working_canvas,
    image_filename,
    horizontal_align="center",
    vertical_align="middle",
    padding_left=0,
    padding_right=0,
    padding_top=0,
    padding_bottom=0,
    scaled_height_percent=None,
):
    """Places a logo element on the canvas.

    Args:
        working_canvas: The global PIL.Image canvas to draw the logo element onto.
        image_filename: The filename of the image to use as our logo element.
        horizontal_align: How to align the image horizontally on the canvas. One of 'left', 'center', or 'right'.
        vertical_align: How to align the image vertically on the canvas. One of 'top', 'middle', or 'bottom'.
        padding_left: How much padding in horizontal canvas percent to add to the left of the logo element.
        padding_right: How much padding in horizontal canvas percent to add to the right of the logo element.
        padding_top: How much padding in vertical canvas percent to add to the top of the logo element.
        padding_bottom: How much padding in vertical canvas percent to add to the bottom of the logo element.
        scaled_height_percent: How tall to make the element in vertical canvas percent.
    """

    # Load the logo element
    logo_image = Image.open(image_filename)

    # Scale the logo element to a percentage of the canvas height if requested
    if scaled_height_percent:
        target_height = round(working_canvas.height / (100 / scaled_height_percent))
        scale_factor = target_height / logo_image.height
        logo_image = ImageOps.scale(logo_image, scale_factor)

    # Calculate the horizontal placement offset. Image origins are at the top-left corner.
    if horizontal_align not in ("left", "right", "center"):
        horizontal_align = "left"

    if horizontal_align == "left":
        h_offset = 0 + percent_to_pixels(
            working_canvas, padding_left, mode="horizontal"
        )
    elif horizontal_align == "center":
        h_offset = round(
            (
                (canvas.width / 2)
                - (logo_image.width / 2)
                + percent_to_pixels(working_canvas, padding_left, mode="horizontal")
                - percent_to_pixels(working_canvas, padding_right, mode="horizontal")
            )
        )
    elif horizontal_align == "right":
        h_offset = round(
            working_canvas.width
            - logo_image.width
            + percent_to_pixels(working_canvas, padding_right, mode="horizontal")
        )

    # Calculate the vertical offset
    if vertical_align not in ("top", "middle", "bottom"):
        vertical_align = "top"

    if vertical_align == "top":
        v_offset = 0 + percent_to_pixels(working_canvas, padding_top, mode="vertical")
    elif vertical_align == "middle":
        v_offset = round(
            ((canvas.height / 2) - (logo_image.height / 2))
            + percent_to_pixels(working_canvas, padding_top, mode="vertical")
            - percent_to_pixels(working_canvas, padding_bottom, mode="vertical")
        )
    elif vertical_align == "bottom":
        v_offset = round(
            working_canvas.height
            - logo_image.height
            - percent_to_pixels(working_canvas, padding_bottom, mode="vertical")
        )

    # Place the image element
    working_canvas.paste(logo_image, (h_offset, v_offset), logo_image)


if __name__ == "__main__":
    # Configure argparse
    parser = argparse.ArgumentParser(
        prog="StartUp Age Background Generator",
        description="Generates a background image for the StartUp Age",
    )

    parser.add_argument(
        "image_filename",
        help="Path to the background image to use. Format must be supported by the Pillow library.",
    )
    parser.add_argument(
        "-O",
        "--output-filename",
        default="output.jpg",
        help="The unscaled output image to be generated.",
    )
    parser.add_argument(
        "-T",
        "--texture-filename",
        default="texture.jpg",
        help="The image to be generated, scaled to a power-of-two size for import into the StartUp Age PRP file.",
    )
    parser.add_argument(
        "-X",
        "--diagnostics",
        action="store_true",
        help="Prints debug messages and outputs a image file with overlays showing the areas covered by the GUI and various aspect ratios.",
    )
    parser.add_argument(
        "-D",
        "--diagnostic-filename",
        default="diagnostic.jpg",
        help="The unscaled output image to be generated with diagnostic overlays applied.",
    )

    args = parser.parse_args()

    # Configure logging
    if args.diagnostics:
        logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    # Set up our canvas
    canvas = Image.new(mode="RGB", size=CANVAS_SIZE)

    # Place the background image
    draw_canvas_background(canvas, args.image_filename)

    # Place the Cyan logo centered on the bottom edge.
    draw_logo_element(
        canvas,
        CYAN_LOGO_FILE,
        horizontal_align="center",
        vertical_align="bottom",
        scaled_height_percent=10,
        padding_bottom=3.5,
    )

    # Save the result
    canvas.save(args.output_filename)
    logging.info(f"Saved unscaled image as {args.texture_filename}")

    # Stetch the image to the desired texture size
    texture = canvas.resize(TEXTURE_SIZE)
    texture.save(args.texture_filename)
    logging.info(f"Saved texture-scaled image as {args.texture_filename}")

    if args.diagnostics:
        # Place the dialog zone
        draw_dialog_zone(canvas)

        # Place the safe zones
        for ratio in ASPECT_RATIOS.keys():
            draw_aspect_ratio_zone(canvas, ratio, ASPECT_RATIOS[ratio])

        # Save the diagnostics file
        canvas.save(args.diagnostic_filename)
        logging.info(f"Saved diagnostic image as {args.diagnostic_filename}")
