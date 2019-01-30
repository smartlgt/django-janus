from setuptools import setup, find_packages
from janus import __version__


setup(
    name="django-janus",
    version='.'.join(str(x) for x in __version__),
    license="BSD",
    description="Janus is a Single sign-on (SSO) system based on django.",
    author="Daniel Leinfelder",
    author_email="daniel@smart-lgt.com",
    url="http://github.com/smartlgt/janus_package",
    zip_safe=False,
    packages=find_packages(),
    package_data={
        "janus": ["janus/templates/*.html", ]},
    install_requires=[
        "django>=2.0",
        "django-oauth-toolkit==1.2.0",
        "django-cors-middleware>=1.3.1",
        "django_python3_ldap>=0.11.2",
        "django-allauth>=0.38.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Framework :: Django",
    ]
)