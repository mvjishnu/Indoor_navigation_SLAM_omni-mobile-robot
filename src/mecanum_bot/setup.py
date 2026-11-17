from glob import glob
import os

from setuptools import find_packages, setup

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
            os.path.join('share', package_name, 'maps'),
            glob('maps/*'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='omni_robot',
    maintainer_email='omni_robot@todo.todo',
    description='Mecanum robot simulation, SLAM and Nav2 navigation',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'cmd_vel_stamper = mecanum_bot.cmd_vel_stamper:main',
        ],
    },
)
