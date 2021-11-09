# PyNGL Demos

All of the pyngl demos in one place. Read the installation instructions below for how to setup and build your python and NGL envrionment.

# Initial setup

I use [pyenv](https://github.com/pyenv/pyenv) to install a local version of python. PyNGL is built and tested using python 3.9.7.

To install pyenv follow the instructions [here](PyEnv.md) but use version 3.9.7 

Once installed your python version should report as follows
```~/.pyenv/shims/python``` and ```python -V```  should report ```Python 3.9.7```

We can now build PyNGL, the main instructions for NGL can be found on [GitHub](https://github.com/NCCA/NGL) however we also need to build the python bindings which are not built by default.

This can be done as follows

```
git clone git@github.com:/NCCA/NGL ~/NGLBuild
cd ~/NGLBuild
mkdir build
 cmake -DCMAKE_INSTALL_PREFIX:PATH=~/NGL -DBUILD_PYNGL=1  -DPYTHON_EXECUTABLE=$(which python) ..
 make -j 8
 make install
```

Finally we need to add the location of the pyngl library to the PYTHONPATH environment variable this can be placed in the .bashrc file

```export PYTHONPATH=$PYTHONPATH:~/NGL/lib```

Once this has been set and source (```source ~/.bashrc```) we can test the install ``` python -c "from pyngl import *"``` should report no errors.

## Demos

The PyNGL demos require a number of python packages to be installed, this can be done using pip3.

|Package  |  Version|
-----------------
glfw  |     2.3.0
numpy |     1.21.4
pip   |     21.2.3
PyOpenGL |  3.1.5
PyQt6  |    6.2.1
PySDL2   |  0.9.9

``` pip3 install PyOpenGL PySDL2 PyQt6 glfw numpy```