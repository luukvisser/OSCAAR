'''
Instructions on how to build Python setup.py's: http://docs.python.org/2/distutils/configfile.html

Run this script to compile the transit light curve function occultquad() from C code
with this command: 

   % python setup.py build_ext --inplace
   
in the OSCAAR/Extras/Examples/sampleData/c directory
test
'''

from distutils.core import setup, Extension

module1 = Extension('transit1forLMLS',
					#define_macros=[('shared',)],
                    #include_dirs = ['/usr/local/include'],
                    #libraries = ['tcl83'],
                    #library_dirs = ['/usr/local/lib'],
                    include_dirs = ['./'],
                    sources = ['transit1forLMLS.c'])

setup (name = 'occultquad',
       version = '1.0',
       description = 'This is quadratic limb-darkening transit light curve model generator.',
       author = 'Brett Morris',
       url = 'http://github.com/oscaar/oscaar',
       long_description = '''
This is quadratic limb-darkening transit light curve model generator.
''',
       ext_modules = [module1])