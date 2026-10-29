from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'mecanum_bot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
                glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'urdf'),
                glob('urdf/*.urdf'),
        ),
        (
            os.path.join('share', package_name, 'meshes'),
            glob('meshes/*'),
        ),
        (
            os.path.join('share', package_name, 'worlds'),
                glob('worlds/*'),
        ),
        (
            os.path.join('share', package_name, 'config'),
                glob('config/*'),
        ),
        (
            os.path.join('share', package_name, 'params'),
                glob('params/*'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='omni_robot',
    maintainer_email='omni_robot@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
