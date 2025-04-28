# RadarStream

RadarStream is a real-time RAWDATA acquisition, processing, and visualization system for TI MIMO mmWave radar series.



https://github.com/user-attachments/assets/7ce99b51-a1af-4025-8a84-ee580eb92d04

Demo1: Real-time Motion Detection and Radar Feature Visualization
<figure>
  <img src="img/4.gif" alt="图片描述" width="100%">
  <figcaption>Demo2: Real-time Gesture Recognition System</figcaption>
</figure>

## Project Overview

This system supports Texas Instruments' MIMO mmWave radar series for real-time raw data acquisition, processing, and visualization. In addition to the RF evaluation board, the DCA1000EVM is required for data capture. Currently, the system has been tested with:
- IWR6843ISK
- IWR6843ISK-OBS

If you encounter any issues while using this project, please feel free to submit a pull request.

## Features

- Real-time radar data acquisition from TI MIMO mmWave radar sensors
- Multi-dimensional feature extraction:
  - Range-Time Information (RTI)
  - Doppler-Time Information (DTI)
  - Range-Doppler Information (RDI)
  - Range-Azimuth Information (RAI)
  - Range-Elevation Information (REI)
- Interactive visualization interface

## Requirements

- Python 3.6+
- PyQt5
- PyQtGraph
- NumPy
- PyTorch
- Matplotlib
- Serial

## Hardware Requirements

- TI MIMO mmWave Radar Sensor (tested with IWR6843ISK and IWR6843ISK-OBS)
- DCA1000 EVM (essential for raw data capture)
- PC with Windows OS (Linux coming  soon)

## Setup and Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install pyqt5 pyqtgraph numpy torch matplotlib pyserial
   ```
3. Connect the mmWave radar sensor and DCA1000 EVM to your computer (only need a 5V 3A DC power wire,  a Ethernet Cable, and a micro USB wire)
4. Configure the network IPv4 settings (referencing the IPv4 configuration process from using mmWaveStudio for the DCA1000 EVM)


<p align="center">
  <img src="img/1.png" width="36%" />
  <img src="img/2.png" width="45%" />
</p>

## 3D Printed Mount

The repository includes STL files for a 3D printed structure designed to mount and secure the DCA1000EVM board.

**Note:** There is a slight error in the DC power hole position. You will need to manually enlarge this hole for proper fit.

<p align="center">
  <img src="img/3.png" width="70%" />
</p>

## Usage

1. Run the main application:
   ```
   python main.py
   ```
2. Select the appropriate COM port for the radar CLI interface
3. Choose a radar configuration file
4. Click "Send Config" to initialize the radar
5. Use the interface to:
   - Visualize radar data in real-time
   - Capture training data for machine learning models


## Project Structure
- `config/`: Configuration files for different radar settings
- `gesture_icons/`: Gesture icons for visualization
- `libs/`: Library files for radar communication
- `STL3D`: 3D printed mount STL files
- `main.py`: Main application entry point
- `real_time_process.py`: Real-time data processing
- `radar_config.py`: Radar configuration utilities
- `iwr6843_tlv/`: TLV protocol implementation for IWR6843
- `dsp/`: Digital signal processing modules
- `UI_interface.py`: PyQt5 user interface


## Citation

If this project helps your research, please consider citing our papers that are closely related to this tool:

```

```


## Acknowledgements

This project references and builds upon:
- [real-time-radar](https://github.com/AndyYu0010/real-time-radar) by AndyYu0010
- [OpenRadar](https://github.com/PreSenseRadar/OpenRadar) - specifically the DSP module

## TODO

Future improvements planned for this project:
- [ ] Validate compatibility with more RF evaluation boards
- [ ] Migrate from PyQt5 to PySide6
- [ ] Make the API in the libs folder more flexible
