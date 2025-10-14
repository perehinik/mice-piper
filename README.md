# Mice Piper

Application for assigning functions to mouse buttons.
This app was created for Logitech MX Master 4.
But it should work with all versions of Logitech MX Master and any other mouse with custom buttons.

You can download latest release here: https://github.com/perehinik/mice-piper/releases

To install on Ubuntu, Mint or any other Debian based OS run

```bash
sudo apt install ./mice-piper_1.0.0_amd64.deb
```

## Usage

After installing the app it runs in the background on debian.
To check app status run

```bash
sudo systemctl status mice-piper
```

You can assign functions to buttons right after installation or by running:

```bash
sudo mice-piper -c
```
