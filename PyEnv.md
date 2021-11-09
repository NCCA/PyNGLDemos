# Install and Setup of PyEnv

PyEnv can be installed by downloading from here https://github.com/pyenv/pyenv or if using a mac use ```brew install pyenv```

If downloading from github do the following

```
git clone https://github.com/pyenv/pyenv.git ~/.pyenv
cd ~/.pyenv && src/configure && make -C src
```

If using homebrew this will be installed into your homebrew path.

## Checking Versions

To see what versions of python are installed we can use 

```
pyenv versions
* system (set by /home/jmacey/.pyenv/version)
```

This show the current installed version of python is the system one, we can confirm this by running 
```
python -V
Python 2.7.5
```

As this is EOL we really need to update and install a better version. The current recommended [vfx reference platform](https://vfxplatform.com/) version is 3.7.x so lets see what versions we have.

```
pyenv versions --list
```

Will list all of the version you will see that there are quite a few, lets filter the list a little with grep

```
pyenv install --list | grep " 3\.[7]
```

This gives use a better list, we are going to install the final 3.7 version which is 3.7.12

We can now install using

```
pyenv install 3.7.12
```

If we want to make this permanent we can add the following to our .bashrc (or .zshrc on mac)

```
eval "$(pyenv init --path)"
```

## Problems

On my mac (M1) I had a few issues, whilst things installed ok when using python 3.7.12 I could not pass all the tests from ```python -m test``` there were some failures. However the main issues was when trying to ```import ctypes``` which failed with an import error.

```
 import ctypes
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/jmacey/.pyenv/versions/3.7.12/lib/python3.7/ctypes/__init__.py", line 7, in <module>
    from _ctypes import Union, Structure, Array
ModuleNotFoundError: No module named '_ctypes'
```

This seems to be an issue with python 3.7 on pyenv. If I test 3.9.x it all works fine as this is supported by Renderman my main python usage I will just use this.
