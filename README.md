# RGBMatrix
## Waveshare RGB Matrix Demo

![video_2026-02-05_00-14-07-ezgif com-optimize](https://github.com/user-attachments/assets/0f3d8e10-d90f-47af-a0d9-0ba1e2966283)

![video_2026-02-05_01-15-32-ezgif com-optimize](https://github.com/user-attachments/assets/eec560a9-b116-4469-a023-418e73ba7682)

<img width="1200" height="896" alt="leddashboard" src="https://github.com/user-attachments/assets/64d2ae93-a0bd-4aa3-82c1-626b89a42200" />

## List of parts
1. Raspbery Pi Pico 2W
2. [Waveshare RGB Matrix P2 64x64](https://www.waveshare.com/wiki/RGB-Matrix-P2-64x64) - 2 pcs

## Connection Diagram

![RGB_Matrix_P2_RPI_Pico01](https://github.com/user-attachments/assets/4335493e-25e0-45ca-979b-47f59255c8a9)

Please solder these wires directly to the Raspberry Pi board if you plan to use my low-profile case.

Please note: if you connect the **VSYS** pin from the Raspberry Pi Pico 2W to the "+" power input for the matrices, you can power both the matrices and the Raspberry Pi directly from the USB supply. No additional power source is required.

The matrices are connected in series using a special cable included in the package. Please pay attention to the direction of the arrows indicating the signal flow. The Pi board must always be connected first, followed by connecting the output of the main display to the slave display.

## Installation

**Prepare the board for CircuitPython.**
1. Connect the Pico 2W to your PC using a USB cable.
2. Use the flash_nuke.uf2 file from the [vendor page](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#pico-2-family) to erase any previous installations on your board.
3. Download version 10 of CircuitPython from the [official site](https://circuitpython.org/board/raspberry_pi_pico2_w/) or from this repository.

**Installing the demo project.**
1. Copy the contents of the repository, except the Firmware folder, to your board.
2. Edit the settings.toml file with your Wi-Fi credentials and timezone settings.
3. Use an IDE, such as this [Online IDE](https://urfdvw.github.io/circuitpython-online-ide-2/), to customize the code.
4. Enable the console in IDE for review the script status and log messages

## Dashboard Case
You can get the 3D-printed model case [here](https://makerworld.com/en/models/2351992-rgb-matrix-clock-dashboard).


