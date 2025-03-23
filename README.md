# PyTimer

https://github.com/user-attachments/assets/05265e74-05f7-4636-ba85-277092f49aa1

I made a PRACTICAL demo for GTK (in this case Python) so that people learning PyGObject
don't have to go through the same pain that I had to go through. Feel free to copy ideas
from this project!

## Flatpak

Available in release section

## Manual
**REQUIRES:**
`meson`
`ninja`
`python`
`sudo privileges`
`GTK/Libadwaita libraries`

First, we must get the source code:
```
git clone https://github.com/code-leech/PyTimer.git
```
Next, we must setup a build directory:
```
meson setup builddir --prefix /usr
```
Next, we must install the app:
```
ninja -C builddir && ninja -C builddir install
```
To uninstall, run:
```
ninja -C builddir && ninja -C builddir uninstall
```

## GNOME BUILDER
Optionally, you can run the project by getting ths source code *(mentioned in Manual section)* and then just run it in there. 

## Maintenance
The only thing I **might** update is the version of the flatpak runtime


