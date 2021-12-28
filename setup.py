from setuptools import setup, find_packages

version = '0.1.dev0'

long_description = (
    open('README.rst').read() + '\n' + open('CHANGES.rst').read() + '\n')

setup(name='cedes.core',
      version=version,
      description="CeDES",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=["Programming Language :: Python", ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['cedes', ],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'cioppino.twothumbs',
          'collective.dexteritytextindexer',
          'eea.facetednavigation',
#          'imio.actionspanel',
          'Plone',
#          'Products.cron4plone',
          'httplib2',
          'pyPdf2',
          'z3c.jbot',
          'xhtml2pdf'
      ],
      extras_require={'test': ['plone.app.testing', 'ipdb', 'zope.globalrequest']},
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
