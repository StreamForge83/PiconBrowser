from setuptools import setup
import setup_translate

pkg = 'Extensions.PiconBrowser'
setup(name='enigma2-plugin-extensions-piconbrowser',
       version='1.0',
       description='extensions-piconbrowser',
       package_dir={pkg: 'PiconBrowser'},
       packages=[pkg],
       package_data={pkg: ['*.png', '*.xml', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass=setup_translate.cmdclass,  # for translation
      )
